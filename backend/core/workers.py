from celery import Celery
from app.database import supabase
from app.crud import insert_analysis_result, update_analysis_status
from app.schemas import (
    AnalysisResult,
    AnalysisStatus,
    Issue,
    IssueSeverity,
    ThreeJSHighlight,
    Vector3,
)
from app.services.geometry_engine_adapter import run_geometry_engine
from dfm import DFMInputs, ToleranceRequest, run_dfm_analysis
from dfm.models import Finding, ProcessType
from geometry.loaders import StepSupportUnavailableError
import tempfile
import os
import requests
import uuid

# Connection to Redis
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "faberai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


# Legacy severity (high / medium / low) → highlight color for the 3D viewer.
_LEGACY_SEVERITY_COLORS = {
    "high": "#ff4d4d",    # blocker
    "medium": "#ffb84d",  # major
    "low": "#4caf50",     # minor
}

_STEP_EXTENSIONS = {"step", "stp"}
_STL_EXTENSIONS = {"stl"}
STEP_UNIT_SCALE_THRESHOLD = 10_000
STEP_MICRON_TO_MM_SCALE = 0.001


def _is_step_dependency_error(exc: BaseException) -> bool:
    """Return True when STEP analysis failed because optional CAD deps are missing."""
    if isinstance(exc, StepSupportUnavailableError):
        return True
    if isinstance(exc, ModuleNotFoundError):
        missing = getattr(exc, "name", "") or ""
        return missing == "OCC" or missing.startswith("OCC.")
    if isinstance(exc, ImportError):
        message = str(exc)
        return "OCC" in message or "pythonocc" in message or "build123d" in message
    return False


def _upload_preview_stl_for_step(step_path: str) -> str | None:
    """Convert a STEP file to STL and upload it for browser preview."""
    preview_path = None
    storage_path = f"previews/{uuid.uuid4()}.stl"
    try:
        from build123d import export_stl, import_step
        from geometry.measurements.bbox import compute_bbox_occ

        shape = import_step(step_path)
        wrapped = getattr(shape, "wrapped", None)
        if wrapped is not None:
            box = compute_bbox_occ(wrapped)
            max_dimension = max(box.width, box.depth, box.height)
            if max_dimension > STEP_UNIT_SCALE_THRESHOLD:
                shape = shape.scale(STEP_MICRON_TO_MM_SCALE)

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_preview:
            preview_path = tmp_preview.name

        if not export_stl(
            shape,
            preview_path,
            tolerance=0.05,
            angular_tolerance=0.25,
            ascii_format=False,
        ):
            print(f"[WORKER] STEP preview STL export returned false for: {step_path}")
            return None

        with open(preview_path, "rb") as preview_file:
            supabase.storage.from_("cad-uploads").upload(
                path=storage_path,
                file=preview_file.read(),
                file_options={"content-type": "model/stl"},
            )

        return supabase.storage.from_("cad-uploads").get_public_url(storage_path)
    except Exception as exc:
        print(f"[WORKER] STEP preview STL generation failed for {step_path}: {exc}")
        return None
    finally:
        if preview_path and os.path.exists(preview_path):
            os.remove(preview_path)


def _build_dfm_inputs(setup_inputs: dict | None) -> DFMInputs | None:
    """Translate UI setup values into the DFM engine input model."""
    if not setup_inputs:
        return None

    process_value = (setup_inputs.get("process") or "").strip().lower()
    process = None
    if process_value == "molding":
        process = ProcessType.injection_molding
    elif process_value == "printing":
        process = ProcessType.printing
    elif process_value in {ProcessType.injection_molding.value, ProcessType.printing.value}:
        process = ProcessType(process_value)

    tolerance_value = (setup_inputs.get("tolerance") or "").strip().lower()
    tolerance_mm = {
        "standard": 0.5,
        "tight": 0.2,
        "precision": 0.1,
    }.get(tolerance_value)
    tolerances: list[ToleranceRequest] = []
    if tolerance_mm is not None:
        tolerances.append(
            ToleranceRequest(
                label="overall part tolerance",
                feature_size_mm=10.0,
                requested_tolerance_mm=tolerance_mm,
            )
        )

    quantity = setup_inputs.get("quantity")
    try:
        quantity_value = int(quantity) if quantity is not None else None
    except (TypeError, ValueError):
        quantity_value = None

    material = (setup_inputs.get("material") or "").strip() or None

    return DFMInputs(
        process=process,
        material=material,
        tolerances=tolerances,
        quantity=quantity_value,
    )


def _finding_to_issue(finding: Finding, rule_id: str) -> Issue:
    """Flatten a single DFM finding into an ``AnalysisResult`` issue.

    The spec severity (blocker / major / minor) is translated to the legacy
    high / medium / low enum through ``Finding.legacy_severity``, which
    consults ``SEVERITY_TO_LEGACY`` from ``dfm.models``.
    """
    legacy = finding.legacy_severity
    ref = finding.geometry_ref

    def _vec3(v):
        """Convert a dfm Vector3-like object to an app.schemas Vector3."""
        if v is None:
            return None
        if isinstance(v, dict):
            return Vector3(x=float(v["x"]), y=float(v["y"]), z=float(v["z"]))
        if isinstance(v, (list, tuple)) and len(v) >= 3:
            return Vector3(x=float(v[0]), y=float(v[1]), z=float(v[2]))
        x = getattr(v, "x", None)
        y = getattr(v, "y", None)
        z = getattr(v, "z", None)
        if x is None or y is None or z is None:
            return None
        return Vector3(x=float(x), y=float(y), z=float(z))

    def _bbox_center(min_point: Vector3 | None, max_point: Vector3 | None) -> Vector3 | None:
        if min_point is None or max_point is None:
            return None
        return Vector3(
            x=(min_point.x + max_point.x) / 2.0,
            y=(min_point.y + max_point.y) / 2.0,
            z=(min_point.z + max_point.z) / 2.0,
        )

    bbox_min = _vec3(ref.bbox_min if ref else None) or Vector3(x=0.0, y=0.0, z=0.0)
    bbox_max = _vec3(ref.bbox_max if ref else None) or Vector3(x=0.0, y=0.0, z=0.0)
    centroid = _vec3(ref.centroid if ref else None) or _bbox_center(bbox_min, bbox_max) or Vector3(x=0.0, y=0.0, z=0.0)

    return Issue(
        issue_id=finding.finding_id,
        type=rule_id,
        severity=IssueSeverity(legacy),
        message=finding.message,
        recommendation=finding.recommendation,
        three_js_highlight=ThreeJSHighlight(
            type="bounding_box",
            color=_LEGACY_SEVERITY_COLORS[legacy],
            min=bbox_min,
            max=bbox_max,
            center=centroid,
        ),
    )


@celery_app.task(
    name="extract_geometry_task",
    bind=True,
    max_retries=3,
    autoretry_for=(
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ),
    retry_kwargs={
        "countdown": 5,
    },
    retry_backoff=True,
    retry_backoff_max=60,     #cap backoff at 60 seconds
    retry_jitter=True,       
)
def extract_geometry_task(
    self,
    file_url: str,
    original_filename: str,
    analysis_id: str,
    setup_inputs: dict | None = None,
):
    """
    Full lifecycle Celery task for CAD file analysis:
    1. Sets status to processing in Supabase
    2. Downloads the CAD file from Supabase Storage into a secure temp file
    3. Passes the temp path to the geometry engine
    4. Saves the result and sets status to completed
    5. On any failure, sets status to failed
    6. Retries automatically on network errors with exponential backoff

    Args:
        file_url: The public Supabase Storage URL of the uploaded CAD file.
        original_filename: The original name of the file for logging.
        analysis_id: The Supabase record ID to update throughout the lifecycle.
    """
    print(f"[WORKER] Starting processing for: {original_filename}")
    update_analysis_status(analysis_id, AnalysisStatus.processing.value)
    print(f"[WORKER] Status set to processing for: {analysis_id}")
    
    file_extension = original_filename.split(".")[-1].lower()
    tmp_path = None

    try:
        #file from Supabase Storage
        print(f"[WORKER] Downloading from: {file_url}")
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}",
            delete=False
        ) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        print(f"[WORKER] File downloaded to temp path: {tmp_path}")

        result = run_geometry_engine(tmp_path, original_filename)
        print(f"[WORKER] Processing complete for: {original_filename}")
        preview_url = file_url if file_extension in _STL_EXTENSIONS else None
        if file_extension in _STEP_EXTENSIONS:
            preview_url = _upload_preview_stl_for_step(tmp_path)
            if preview_url:
                result["preview_url"] = preview_url

        # DFM rule engine runs downstream of geometry, on its output only.
        # A failure here must not lose the geometry result, so it degrades to
        # no report rather than failing the task.
        dfm_report = None
        issues = []
        score = result.get("mock_score")
        try:
            dfm_inputs = _build_dfm_inputs(setup_inputs)
            report = run_dfm_analysis(
                result,
                inputs=dfm_inputs,
                analysis_id=analysis_id,
            )
            dfm_report = report.model_dump(mode="json")
            score = report.manufacturability_score
            # Flatten DFM findings into AnalysisResult.issues, translating
            # the spec's blocker/major/minor severity to the legacy
            # high/medium/low enum via Finding.legacy_severity.
            for process_report in report.processes:
                for rule_result in process_report.rule_results:
                    for finding in rule_result.findings:
                        issues.append(
                            _finding_to_issue(finding, rule_result.rule_id)
                        )
            print(
                f"[WORKER] DFM analysis complete for {original_filename}: "
                f"score {score}, manufacturable={report.manufacturable}"
            )
        except Exception as exc:
            print(f"[WORKER] DFM analysis failed for {original_filename}: {exc}")

        # Build a complete AnalysisResult that carries the geometry payload
        # inside geometry_data so the API can round-trip it without stripping fields.
        analysis_result = AnalysisResult(
            analysis_id=analysis_id,
            filename=original_filename,
            status=AnalysisStatus.completed,
            manufacturability_score=score,
            file_url=preview_url,
            source_file_url=file_url,
            printing_manufacturable=report.printing_manufacturable if dfm_report is not None else None,
            printing_score=report.printing_score if dfm_report is not None else None,
            molding_manufacturable=report.molding_manufacturable if dfm_report is not None else None,
            molding_score=report.molding_score if dfm_report is not None else None,
            geometry_data=result,
            dfm_report=dfm_report,
            issues=issues,
        )

        update_analysis_status(
            analysis_id,
            AnalysisStatus.completed.value,
            extra_fields={
                "manufacturability_score": score,
                "results_json": analysis_result.model_dump(),
            }
        )
        print(f"[WORKER] Status set to completed for: {analysis_id}")

        return analysis_result.model_dump()

    except Exception as exc:
        if _is_step_dependency_error(exc):
            # Missing optional STEP dependencies won't be fixed by retrying:
            # mark the analysis failed immediately so the client sees FAILED
            # instead of a record stuck in "processing".
            print(f"[WORKER] Cannot process {original_filename}: {exc}")
            update_analysis_status(analysis_id, AnalysisStatus.failed.value)
            raise

        if self.request.retries >= self.max_retries:
            print(f"[WORKER] All retries exhausted for: {original_filename}. Marking as failed.")
            update_analysis_status(
                analysis_id,
                AnalysisStatus.failed.value,
            )
        else:
            print(f"[WORKER] Error on attempt {self.request.retries + 1}, retrying: {exc}")
        raise

    finally:
        # Always clean up the temp file, even if processing fails
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f"[WORKER] Temp file deleted: {tmp_path}")
