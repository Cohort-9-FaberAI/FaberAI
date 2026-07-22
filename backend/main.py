import logging

from celery.result import AsyncResult
from fastapi import FastAPI, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from postgrest.exceptions import APIError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.workers import celery_app, extract_geometry_task
from app.schemas import AnalysisResult, AnalysisStatus
from app.crud import insert_analysis_result, get_analysis_by_id
from app.services.storage import upload_cad_file_to_storage

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FaberAI Backend",
    description="AI-powered manufacturability review API for CAD parts.",
    version="0.1.0",
)

# 🚨 Configuração do CORS para não travar as requisições do frontend localmente
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
        "filename": "sample_bracket.stl",
        "status": "completed",
        "manufacturability_score": 72,
        "summary": "Part is mostly manufacturable. 3 issues found that may require design changes.",
        "file_url": "https://storage.googleapis.com/makerbot-public-assets/cad-models/hinge.stl",
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
                "centroid": [15.2, 4.1, 0.0]
            },
            {
                "issue_id": "err_002",
                "severity": "major",
                "title": "Sharp Internal Corner",
                "description": "Requires a fillet to reduce stress concentration.",
                "edge_id": 232,
                "centroid": [-5.0, 10.5, 3.2]
            },
            {
                "issue_id": "err_003",
                "severity": "minor",
                "title": "Non-Standard Draft Angle",
                "description": "Draft angle is 1.5 degrees, but recommended is 2.0.",
                "face_id": 45,
                "centroid": [0.0, -12.3, 5.0]
            }
        ]
    }

@app.post("/analysis/", tags=["Analysis"])
def create_analysis(result: AnalysisResult):
    """
    Accepts a validated analysis result payload and stores it in Supabase.
    Used to verify DB integration is working correctly.
    """
    inserted = insert_analysis_result(result)
    return {"message": "Analysis result saved successfully.", "data": inserted}