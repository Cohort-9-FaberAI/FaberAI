import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from postgrest.exceptions import APIError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.workers import celery_app, extract_geometry_task
from app.schemas import AnalysisResult, AnalysisStatus
from app.crud import insert_analysis_result, get_analysis_by_id
from app.services.ai import AIAnswer, answer_dfm_question
from app.services.dfm_knowledge import KnowledgeAnswer, answer_dfm_knowledge_question
from app.services.storage import upload_cad_file_to_storage
from dfm import DFMInputs, DFMReport, load_dfm_config, run_dfm_analysis
from fastapi.responses import FileResponse
from app.observability import setup_langtrace

setup_langtrace()
logger = logging.getLogger(__name__)


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
    yield


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
)


def _error_response(status_code: int, error_type: str, message, details=None) -> JSONResponse:
    """
    Builds the standardized error envelope used by all exception handlers:
    {"error": {"code": <int>, "type": <slug>, "message": <str>, "details": <optional>}}
    """
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

@app.post("/upload/", status_code=status.HTTP_202_ACCEPTED, tags=["Upload"])
async def upload_cad_file(file: UploadFile):
    """
    Accepts a CAD file (STEP or STL), uploads it to Supabase Storage,
    creates a pending record in Supabase, and dispatches a background
    Celery task for geometry analysis.
    Returns the task ID and analysis ID for status polling.
    """
    # Upload file to Supabase Storage and get back the URL
    upload_result = upload_cad_file_to_storage(file)

    # Create a pending record in Supabase before dispatching the task
    analysis = AnalysisResult(
        filename=upload_result["original_filename"],
        status=AnalysisStatus.pending,
    )
    insert_analysis_result(analysis)

    # Pass analysis_id to the worker so it can update the record
    task = extract_geometry_task.delay(
        upload_result["public_url"],
        upload_result["original_filename"],
        analysis.analysis_id,
    )

    return {
        "message": "File received and uploaded successfully. Processing started in background.",
        "task_id": task.id,
        "analysis_id": analysis.analysis_id,
        "filename": upload_result["original_filename"],
        "storage_path": upload_result["storage_path"],
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
                    analysis = AnalysisResult.model_validate(results_json)
                    return {"task_id": task_id, "status": "SUCCESS", "analysis_id": analysis_id, "result": analysis}
                return {"task_id": task_id, "status": "SUCCESS", "analysis_id": analysis_id}

            if db_status == "failed":
                return {"task_id": task_id, "status": "FAILED", "analysis_id": analysis_id}

            if db_status in {"pending", "processing"}:
                return {"task_id": task_id, "status": "PROCESSING", "analysis_id": analysis_id}

    if state == "FAILURE":
        # Keep the raw exception in server logs only; never expose it to clients.
        logger.error(
            "Task %s failed: %s\n%s", task_id, task_result.result, task_result.traceback
        )
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": "Analysis failed. Please try again later.",
        }

    if state == "SUCCESS":
        task_output = task_result.result
        resolved_analysis_id = (
            task_output.get("analysis_id", analysis_id or task_id)
            if isinstance(task_output, dict)
            else analysis_id or task_id
        )

        try:
            record = get_analysis_by_id(resolved_analysis_id)
        except APIError:
            record = None

        if record is not None and record.get("results_json"):
            analysis = AnalysisResult.model_validate(record["results_json"])
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


def _load_stored_analysis(analysis_id: str) -> dict:
    try:
        record = get_analysis_by_id(analysis_id)
    except APIError as exc:
        logger.error("Failed to load analysis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the analysis store. Please try again.",
        ) from exc

    if not record or not record.get("results_json"):
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


# ---------------------------------------------------------------------------
# AI endpoint
# ---------------------------------------------------------------------------

@app.post("/ai/ask", response_model=AIAnswer, tags=["AI"])
def ask_faber_ai(request: AIAskRequest):
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

    return answer_dfm_question(
        report=report,
        question=request.question,
        geometry=geometry if isinstance(geometry, dict) else None,
        analysis_id=request.analysis_id,
    )



# ---------------------------------------------------------------------------
# DFM reference-standards knowledge base (RAG over ASME etc.)
# ---------------------------------------------------------------------------

class KnowledgeAskRequest(BaseModel):
    """Ask a general DFM/GD&T question against the ingested reference standards.

    Unlike /ai/ask, this is not scoped to a specific part's report — it's a
    lookup against the standards themselves (e.g. "what's the max positional
    tolerance for a clearance hole?").
    """

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    source: Optional[str] = Field(
        default=None, description='Restrict to one ingested source, e.g. "ASME Y14.5-2018".'
    )


@app.post("/dfm/knowledge/ask", response_model=KnowledgeAnswer, tags=["AI"])
def ask_dfm_knowledge(request: KnowledgeAskRequest):
    """Answer a DFM/GD&T question from the ingested reference standards.

    Retrieves the most similar chunks from dfm_reference_docs (populated by
    app/services/dfm_knowledge/ingest.py) and answers from them only — it
    never reasons about a specific uploaded part.
    """
    return answer_dfm_knowledge_question(
        question=request.question,
        top_k=request.top_k,
        source=request.source,
    )


@app.get("/mock-file", tags=["Analysis (Mock)"])
def get_mock_file():
    """
    Serves the mock STL file directly to bypass CORS during local development.
    """
    
    file_path = "datasets/STL/box_prism.stl" 
    return FileResponse(path=file_path, media_type="application/octet-stream", filename="box_prism.stl")