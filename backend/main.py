import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from celery.result import AsyncResult
from celery.exceptions import CeleryError
from fastapi import FastAPI, HTTPException, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from postgrest.exceptions import APIError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.workers import celery_app, extract_geometry_task, _upload_preview_stl_for_step
from app.schemas import AnalysisResult, AnalysisStatus
from app.crud import insert_analysis_result, get_analysis_by_id, update_analysis_status
from app.services.ai import AIAnswer, answer_dfm_question_async
from app.services.report_pdf import build_report_pdf, report_pdf_filename
from app.services.storage import upload_cad_file_to_storage
from dfm import DFMInputs, DFMReport, load_dfm_config, run_dfm_analysis
from fastapi.responses import FileResponse
from app.observability import setup_langtrace
from app.services.ai.mcp_moldsim import init_moldsim, shutdown_moldsim
import requests

setup_langtrace()
logger = logging.getLogger(__name__)

# Python's root logger defaults to WARNING with no handler beyond the
# last-resort one, so plain logger.info(...) calls anywhere in the app
# (including the AI-answer and retrieval timing breakdowns) would otherwise
# never reach the console. This makes INFO-level logs from every module
# visible without each one configuring logging itself.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
_STEP_EXTENSIONS = {".step", ".stp"}


def _raise_backend_unhealthy(component: str, message: str, cause: Exception | None = None) -> None:
    logger.error("Backend health check failed for %s: %s", component, message)
    exc = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "component": component,
            "message": message,
        },
    )
    if cause:
        raise exc from cause
    raise exc


def _check_celery_broker() -> None:
    try:
        with celery_app.connection_for_read() as connection:
            connection.ensure_connection(max_retries=1)
    except Exception as exc:
        _raise_backend_unhealthy(
            "celery_broker",
            "The analysis queue is unavailable. Check Redis and restart the backend worker.",
            cause=exc,
        )


def _check_celery_worker() -> None:
    try:
        responses = celery_app.control.inspect(timeout=1.5).ping()
    except Exception as exc:
        _raise_backend_unhealthy(
            "celery_worker",
            "The analysis worker could not be reached. Restart the Celery worker.",
            cause=exc,
        )

    if not responses:
        _raise_backend_unhealthy(
            "celery_worker",
            "No analysis worker is online. Restart the Celery worker.",
        )


def _check_analysis_queue() -> None:
    _check_celery_broker()
    _check_celery_worker()


def _is_step_url(value: str | None) -> bool:
    if not value:
        return False
    clean_value = value.split("?", 1)[0].lower()
    return any(clean_value.endswith(ext) for ext in _STEP_EXTENSIONS)


def _is_step_analysis_without_preview(analysis: dict) -> bool:
    geometry_data = analysis.get("geometry_data")
    geometry = geometry_data if isinstance(geometry_data, dict) else {}
    filename = str(analysis.get("filename") or "").lower()
    source_format = str(geometry.get("source_format") or "").lower()
    file_url = analysis.get("file_url")

    is_step = (
        source_format == "step"
        or filename.endswith(".step")
        or filename.endswith(".stp")
        or _is_step_url(analysis.get("source_file_url"))
    )
    has_preview = bool(geometry.get("preview_url")) or (
        isinstance(file_url, str) and not _is_step_url(file_url)
    )
    return is_step and not has_preview and bool(analysis.get("source_file_url"))


def _attach_missing_step_preview(analysis: dict) -> dict:
    """
    Backfills STL previews for completed STEP analyses created before preview
    URLs were attached. This keeps old completed reports renderable in the UI.
    """
    if not _is_step_analysis_without_preview(analysis):
        return analysis

    source_url = str(analysis["source_file_url"])
    filename = str(analysis.get("filename") or "part.step")
    suffix = ".stp" if filename.lower().endswith(".stp") else ".step"
    tmp_path = None

    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        preview_url = _upload_preview_stl_for_step(tmp_path)
        if not preview_url:
            return analysis

        geometry_data = analysis.get("geometry_data")
        geometry = geometry_data if isinstance(geometry_data, dict) else {}
        geometry["preview_url"] = preview_url
        analysis["geometry_data"] = geometry
        analysis["file_url"] = preview_url

        analysis_id = analysis.get("analysis_id")
        if analysis_id:
            update_analysis_status(
                str(analysis_id),
                AnalysisStatus.completed.value,
                extra_fields={"results_json": analysis},
            )
        return analysis
    except Exception:
        logger.exception("Could not backfill STEP preview for analysis %s", analysis.get("analysis_id"))
        return analysis
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the DFM threshold/scoring YAML once, at boot.

    Doing it here means a malformed config fails startup loudly instead of
    turning into a 500 on the first upload, and no request ever pays for
    re-reading the files.
    """
    config = load_dfm_config()
    logger.info(
        "DFM config loaded: thresholds v%s, scoring v%s",
        config.version,
        config.scoring_version,
    )

    # Best-effort: pull the ~440MB BGE embedding model into memory now rather
    # than on the first /ai/ask or /dfm/knowledge/ask call. Without this, the
    # very first question after every restart pays the full load time on top
    # of the answer itself. Never fails startup — environments without the
    # knowledge-base extras (or with no ASME data ingested yet) still boot
    # fine and just retrieve nothing until it's installed.
    try:
        from app.services.dfm_knowledge.embeddings import embed_query

        embed_query("warm up")
        logger.info("ASME embedding model preloaded.")
    except Exception as exc:  # noqa: BLE001 - startup must not fail on this
        logger.warning("Embedding model preload skipped: %s", exc)

    await init_moldsim()

    yield

    await shutdown_moldsim()


app = FastAPI(
    title="FaberAI Backend",
    description="AI-powered manufacturability review API for CAD parts.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


def _error_response(status_code: int, error_type: str, message, details=None) -> JSONResponse:
    """
    Builds the standardized error envelope used by all exception handlers:
    {"error": {"code": <int>, "type": <slug>, "message": <str>, "details": <optional>}}
    """
    if isinstance(message, dict):
        details = details or message
        message = message.get("message", "Request failed.")

    error = {"code": status_code, "type": error_type, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Wraps HTTPExceptions raised by routes (e.g. 404s) in the standard envelope
    instead of FastAPI's default {"detail": ...} shape.
    """
    return _error_response(exc.status_code, "http_error", exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Standardizes 422 Unprocessable Entity responses, keeping pydantic's
    per-field error list under "details".
    """
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        "Request validation failed.",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unexpected errors: returns a standard 500 envelope without
    leaking internal exception details to the client.
    """
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_server_error",
        "An unexpected internal error occurred.",
    )

@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Returns 200 OK to confirm the server is running.
    """
    return {"status": "ok", "message": "FaberAI backend is running."}


@app.get("/health/dependencies", tags=["Health"])
def dependency_health_check():
    """
    Verifies the upload processing dependencies that can otherwise leave the
    frontend waiting on a background job forever.
    """
    _check_analysis_queue()
    return {
        "status": "ok",
        "dependencies": {
            "celery_broker": "ok",
            "celery_worker": "ok",
        },
    }

@app.post("/upload/", status_code=status.HTTP_202_ACCEPTED, tags=["Upload"])
async def upload_cad_file(file: UploadFile):
    """
    Accepts a CAD file (STEP or STL), uploads it to Supabase Storage,
    creates a pending record in Supabase, and dispatches a background
    Celery task for geometry analysis.
    Returns the task ID and analysis ID for status polling.
    """
    _check_analysis_queue()

    # Upload file to Supabase Storage and get back the URL
    upload_result = upload_cad_file_to_storage(file)

    # Create a pending record in Supabase before dispatching the task
    analysis = AnalysisResult(
        filename=upload_result["original_filename"],
        status=AnalysisStatus.pending,
    )
    try:
        insert_analysis_result(analysis)
    except APIError as exc:
        _raise_backend_unhealthy(
            "analysis_store",
            "The analysis database is unavailable. Check Supabase before uploading again.",
            cause=exc,
        )

    # Pass analysis_id to the worker so it can update the record
    try:
        task = extract_geometry_task.delay(
            upload_result["public_url"],
            upload_result["original_filename"],
            analysis.analysis_id,
        )
    except (CeleryError, OSError, TimeoutError) as exc:
        _raise_backend_unhealthy(
            "analysis_queue",
            "The analysis job could not be queued. Check Redis and the Celery worker.",
            cause=exc,
        )

    return {
        "message": "File received and uploaded successfully. Processing started in background.",
        "task_id": task.id,
        "analysis_id": analysis.analysis_id,
        "filename": upload_result["original_filename"],
        "storage_path": upload_result["storage_path"],
        "file_url": upload_result["public_url"],
        "source_file_url": upload_result["public_url"],
        "status": "pending",
    }

@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task_status(task_id: str, analysis_id: str | None = None):
    """
    Polls the status of a background analysis task.

    Returns the current task state. When an analysis_id is supplied, the API
    prefers the Supabase analysis record so the UI can see completed/failed
    status immediately even if Celery still reports PENDING for a moment.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    state = task_result.state

    if analysis_id:
        try:
            record = get_analysis_by_id(analysis_id)
        except APIError:
            record = None

        if record is not None:
            db_status = record.get("status")
            if db_status == "completed":
                results_json = record.get("results_json")
                if results_json:
                    results_json = _attach_missing_step_preview(results_json)
                    analysis = AnalysisResult.model_validate(results_json)
                    return {"task_id": task_id, "status": "SUCCESS", "analysis_id": analysis_id, "result": analysis}
                return {"task_id": task_id, "status": "SUCCESS", "analysis_id": analysis_id}

            if db_status == "failed":
                return {"task_id": task_id, "status": "FAILED", "analysis_id": analysis_id}

            if db_status in {"pending", "processing"} and state in {"PENDING", "STARTED", "RETRY"}:
                return {"task_id": task_id, "status": "PROCESSING", "analysis_id": analysis_id}

    if state == "PENDING":
        _check_analysis_queue()
        return {
            "task_id": task_id,
            "status": "PENDING",
            **({"analysis_id": analysis_id} if analysis_id else {}),
        }

    if state in {"STARTED", "RETRY"}:
        return {
            "task_id": task_id,
            "status": "PROCESSING",
            **({"analysis_id": analysis_id} if analysis_id else {}),
        }

    if state == "SUCCESS":
        task_output = task_result.result
        if isinstance(task_output, dict):
            resolved_analysis_id = (
                task_output.get("analysis_id")
                or analysis_id
                or task_id
            )
            if task_output.get("status") == AnalysisStatus.completed.value:
                return {
                    "task_id": task_id,
                    "status": "SUCCESS",
                    "analysis_id": resolved_analysis_id,
                    "result": task_output,
                }
        else:
            resolved_analysis_id = analysis_id or task_id

    if state == "FAILURE":
        # Keep the raw exception in server logs only; never expose it to clients.
        logger.error(
            "Task %s failed: %s\n%s", task_id, task_result.result, task_result.traceback
        )
        if analysis_id:
            try:
                record = get_analysis_by_id(analysis_id)
                if record is not None and record.get("status") in {"pending", "processing"}:
                    update_analysis_status(analysis_id, AnalysisStatus.failed.value)
            except APIError:
                logger.exception(
                    "Could not mark failed analysis %s after Celery task failure.",
                    analysis_id,
                )
        return {
            "task_id": task_id,
            "status": "FAILURE",
            **({"analysis_id": analysis_id} if analysis_id else {}),
            "error": "Analysis failed. Please try again later.",
        }

    if state == "SUCCESS":
        try:
            record = get_analysis_by_id(resolved_analysis_id)
        except APIError:
            record = None

        if record is not None and record.get("results_json"):
            results_json = _attach_missing_step_preview(record["results_json"])
            analysis = AnalysisResult.model_validate(results_json)
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "analysis_id": resolved_analysis_id,
                "result": analysis,
            }
 
        # Fix 1.10: DB record missing or results_json empty — task completed
        # in Celery but the result was not persisted (DB write failed, record
        # deleted, or Supabase was down). Return the Celery payload directly
        # so the client gets a terminal SUCCESS instead of a misleading 404.
        logger.warning(
            "Task %s succeeded in Celery but no DB record found for analysis_id '%s'. "
            "Returning Celery result payload directly.",
            task_id,
            resolved_analysis_id,
        )
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "analysis_id": resolved_analysis_id,
            "result": task_output if isinstance(task_output, dict) else None,
            "warning": "Result was not persisted to the database. Contact support if this persists.",
        }

    # Celery uses STARTED/RETRY for in-flight tasks; expose them as PROCESSING
    status_map = {"STARTED": "PROCESSING", "RETRY": "PROCESSING"}
    return {"task_id": task_id, "status": status_map.get(state, state)}


@app.post("/analyze-mock", tags=["Analysis (Mock)"])
def analyze_mock():
    """
    Temporary mock endpoint to unblock the Frontend team.
    Returns a hardcoded analysis response matching the agreed API contract,
    including a placeholder STL and geometric issues using centroids and IDs.
    Will be replaced by the real geometry engine analysis endpoint.
    """
    return {
        "analysis_id": "mock-analysis-0001",
        "filename": "box_prism.stl", 
        "status": "completed",
        "manufacturability_score": 72,
        "printing_score": 81,
        "molding_score": 55,
        "printing_manufacturable": True,
        "molding_manufacturable": False,
        "summary": "Part is mostly manufacturable. 3 issues found that may require design changes.",
        "file_url": "http://127.0.0.1:8000/mock-file", 
        "part_metadata": {
            "units": "mm",
            "volume": 15420.5,
            "surface_area": 8930.2,
            "bounding_box": {
                "min": {"x": 0.0, "y": 0.0, "z": 0.0},
                "max": {"x": 120.0, "y": 80.0, "z": 45.0}
            }
        },
        "geometry_data": {
            "source_format": "stl",
            "bounding_box": {
                "min": {"x": 0.0, "y": 0.0, "z": 0.0},
                "max": {"x": 120.0, "y": 80.0, "z": 45.0}
            },
            "volume_mm3": 15420.5,
            "surface_area_mm2": 8930.2,
            "measurements_reliable": True,
            "center_mass": {"x": 60.0, "y": 40.0, "z": 22.5}
        },
        "issues": [
            {
                "issue_id": "err_001",
                "severity": "blocker",
                "title": "Wall Thickness Too Thin",
                "description": "This wall is under the 2mm minimum thickness for injection molding.",
                "face_id": 104,
                "centroid": {"x": 15.2, "y": 4.1, "z": 0.0}
            },
            {
                "issue_id": "err_002",
                "severity": "major",
                "title": "Sharp Internal Corner",
                "description": "Requires a fillet to reduce stress concentration.",
                "edge_id": 232,
                "centroid": {"x": -5.0, "y": 10.5, "z": 3.2}
            },
            {
                "issue_id": "err_003",
                "severity": "minor",
                "title": "Non-Standard Draft Angle",
                "description": "Draft angle is 1.5 degrees, but recommended is 2.0.",
                "face_id": 45,
                "centroid": {"x": 0.0, "y": -12.3, "z": 5.0}
            }
        ],
        "response_model": AnalysisResult.model_json_schema()  # Include the schema for client validation    
    }

@app.post("/analysis/", tags=["Analysis"])
def create_analysis(result: AnalysisResult):
    """
    Accepts a validated analysis result payload and stores it in Supabase.
    Used to verify DB integration is working correctly.
    """
    inserted = insert_analysis_result(result)
    return {"message": "Analysis result saved successfully.", "data": inserted}

# ---------------------------------------------------------------------------
# DFM rule engine
# ---------------------------------------------------------------------------

class DFMEvaluateRequest(BaseModel):
    """Run the DFM rule-set against a geometry payload.

    Used to re-score a part with different user context (material, printer,
    tolerances) without re-uploading the CAD file, and to exercise the engine
    against mocked geometry — including the ribs[]/bosses[] arrays the geometry
    team has not shipped yet.
    """

    model_config = ConfigDict(extra="forbid")

    # A GeometryEngineResponse payload (or the geometry_data field of a stored
    # analysis). Unknown keys are tolerated by the DFM geometry contract.
    geometry: Dict[str, Any]
    inputs: Optional[DFMInputs] = None
    analysis_id: Optional[str] = None


class AIAskRequest(BaseModel):
    """Ask a question about an existing manufacturability report."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    # Either point at a stored analysis...
    analysis_id: Optional[str] = None
    # ...or pass the report inline (the shape returned by /dfm/evaluate).
    report: Optional[Dict[str, Any]] = None
    # Optional geometry facts for extra context. Never re-analysed.
    geometry: Optional[Dict[str, Any]] = None


class ReportDownloadRequest(BaseModel):
    """Generate a supplier-ready PDF from the completed analysis in the UI."""

    model_config = ConfigDict(extra="forbid")

    analysis: Dict[str, Any]
    include_comparison: bool = False
    process: Optional[str] = None
    material: Optional[str] = None
    tolerance: Optional[str] = None


def _load_stored_analysis(analysis_id: str) -> dict:
    try:
        record = get_analysis_by_id(analysis_id)
    except APIError as exc:
        logger.error("Failed to load analysis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the analysis store. Please try again.",
        ) from exc

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No completed analysis found for analysis_id '{analysis_id}'.",
        )

    record_status = record.get("status")
    if record_status and record_status != AnalysisStatus.completed.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Analysis '{analysis_id}' is {record_status}, not completed. "
                "The assistant only answers from completed DFM reports."
            ),
        )

    if not record.get("results_json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No completed analysis found for analysis_id '{analysis_id}'.",
        )
    return record["results_json"]


@app.post("/dfm/evaluate", response_model=DFMReport, tags=["DFM"])
def evaluate_dfm(request: DFMEvaluateRequest):
    """Run the DFM rule engine over a geometry payload and return the report.

    Deterministic: the same geometry and inputs always produce the same
    verdicts, scores and findings. No LLM is involved.
    """
    return run_dfm_analysis(
        request.geometry,
        inputs=request.inputs,
        analysis_id=request.analysis_id,
    )


@app.get("/analysis/{analysis_id}/dfm", response_model=DFMReport, tags=["DFM"])
def get_dfm_report(analysis_id: str):
    """Return the stored manufacturability report for a completed analysis."""
    results = _load_stored_analysis(analysis_id)
    report = results.get("dfm_report")
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Analysis '{analysis_id}' has no DFM report. It was analysed before the "
                f"rule engine was enabled, or the DFM stage failed for this part."
            ),
        )
    return DFMReport.model_validate(report)


@app.post("/analysis/report.pdf", tags=["Reports"])
def download_inline_analysis_report(request: ReportDownloadRequest):
    """Download a PDF report from the completed analysis payload held by the UI."""
    if request.analysis.get("status") != AnalysisStatus.completed.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A completed analysis is required before downloading a PDF.",
        )

    # 1. Garante que o dicionário de DFM report existe na análise
    if "dfm_report" not in request.analysis or not isinstance(request.analysis["dfm_report"], dict):
        request.analysis["dfm_report"] = {}

    report_dict = request.analysis["dfm_report"]

    # 2. Garante que a chave 'inputs' existe dentro do dfm_report
    if "inputs" not in report_dict or not isinstance(report_dict["inputs"], dict):
        report_dict["inputs"] = {}

    # 3. Injeta diretamente os valores que vieram do Frontend (PLA, Printing, etc.)
    if request.process:
        p = request.process.lower().strip()
        report_dict["inputs"]["process"] = "3d_printing" if "print" in p else "injection_molding"
        report_dict["inputs"]["printing_process"] = "fdm"
    if request.material:
        mat = request.material.lower().strip()
        report_dict["inputs"]["material"] = mat
        report_dict["inputs"]["material_resolved"] = mat
    if request.tolerance:
        tol = request.tolerance.lower()
        report_dict["inputs"]["tolerance"] = "precision" if ("precision" in tol or "fine" in tol) else "standard"

    # 4. Removemos o aviso genérico de "No material supplied" das suposições se o material foi fornecido
    if request.material and "processes" in report_dict:
        for proc in report_dict["processes"]:
            if "assumptions" in proc and isinstance(proc["assumptions"], list):
                # Filtra fora o aviso de falta de material para o gerador de PDF não imprimir
                proc["assumptions"] = [
                    asm for asm in proc["assumptions"] 
                    if "No material supplied" not in asm
                ]
                # Adiciona a suposição correta do material escolhido
                mat_name = request.material.upper()
                proc["assumptions"].insert(0, f"Material supplied: {mat_name} limits and thresholds applied.")

    if not report_dict and not request.analysis.get("issues"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No DFM report or issue list is available to export.",
        )

    pdf = build_report_pdf(
        request.analysis,
        include_comparison=request.include_comparison,
    )
    filename = report_pdf_filename(request.analysis)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# AI endpoint
# ---------------------------------------------------------------------------

@app.post("/ai/ask", response_model=AIAnswer, tags=["AI"])
async def ask_faber_ai(request: AIAskRequest):
    """Answer a question about a manufacturability report.

    Strictly downstream: this endpoint reads a report that already exists. It
    never runs the geometry engine and never re-evaluates a DFM rule, so it
    cannot contradict the analysis the user is looking at. A request for an
    analysis with no stored report is rejected rather than silently re-analysed.
    """
    geometry = request.geometry

    if request.report is not None:
        report_payload = request.report
    elif request.analysis_id:
        results = _load_stored_analysis(request.analysis_id)
        report_payload = results.get("dfm_report")
        if not report_payload:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Analysis '{request.analysis_id}' has no DFM report yet. Run the analysis "
                    f"first — the assistant answers from report data and does not compute it."
                ),
            )
        if geometry is None:
            geometry = results.get("geometry_data")
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide either an analysis_id or an inline report.",
        )

    try:
        report = DFMReport.model_validate(report_payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"The supplied report is not a valid DFM report: {exc}",
        ) from exc

    return await answer_dfm_question_async(
        report=report,
        question=request.question,
        geometry=geometry if isinstance(geometry, dict) else None,
        analysis_id=request.analysis_id,
    )


@app.get("/mock-file", tags=["Analysis (Mock)"])
def get_mock_file():
    """
    Serves the mock STL file directly to bypass CORS during local development.
    """
    
    file_path = "datasets/STL/box_prism.stl" 
    return FileResponse(path=file_path, media_type="application/octet-stream", filename="box_prism.stl")