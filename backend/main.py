from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.workers import celery_app, extract_geometry_task
from app.schemas import AnalysisResult, AnalysisStatus
from app.crud import insert_analysis_result, get_analysis_by_id, update_analysis_status
from app.services.storage import upload_cad_file_to_storage

app = FastAPI(
    title="FaberAI Backend",
    description="AI-powered manufacturability review API for CAD parts.",
    version="0.1.0",
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
def get_task_status(task_id: str):
    """
    Polls the status of a background analysis task.

    Returns the current Celery state (PENDING, PROCESSING, SUCCESS, FAILURE).
    On SUCCESS, fetches the final validated analysis result from Supabase.
    Note: Celery reports unknown task ids as PENDING, so a 404 is only
    possible once a task has finished but no stored result can be found.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    state = task_result.state

    if state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(task_result.result),
        }

    if state == "SUCCESS":
        task_output = task_result.result
        analysis_id = (
            task_output.get("analysis_id", task_id)
            if isinstance(task_output, dict)
            else task_id
        )

        try:
            record = get_analysis_by_id(analysis_id)
        except APIError:
            record = None

        if record is None or not record.get("results_json"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis result found for task '{task_id}'.",
            )

        analysis = AnalysisResult.model_validate(record["results_json"])
        return {"task_id": task_id, "status": "SUCCESS", "result": analysis}

    # Celery uses STARTED/RETRY for in-flight tasks; expose them as PROCESSING
    status_map = {"STARTED": "PROCESSING", "RETRY": "PROCESSING"}
    return {"task_id": task_id, "status": status_map.get(state, state)}


@app.post("/analyze-mock", tags=["Analysis (Mock)"])
def analyze_mock():
    """
    Temporary mock endpoint to unblock the Frontend team.
    Returns a hardcoded analysis response matching the agreed API contract,
    including dummy three_js_highlight bounding boxes for the 3D canvas.
    Will be replaced by the real geometry engine analysis endpoint.
    """
    return {
        "analysis_id": "mock-analysis-0001",
        "filename": "sample_bracket.stl",
        "status": "completed",
        "manufacturability_score": 72,
        "summary": "Part is mostly manufacturable. 2 issues found that may require design changes.",
        "part_metadata": {
            "units": "mm",
            "volume": 15420.5,
            "surface_area": 8930.2,
            "bounding_box": {
                "min": {"x": 0.0, "y": 0.0, "z": 0.0},
                "max": {"x": 120.0, "y": 80.0, "z": 45.0}
            }
        },
        "issues": [
            {
                "issue_id": "issue-001",
                "type": "thin_wall",
                "severity": "high",
                "message": "Wall thickness of 0.8mm is below the minimum of 1.5mm for CNC machining.",
                "recommendation": "Increase wall thickness to at least 1.5mm.",
                "three_js_highlight": {
                    "type": "bounding_box",
                    "color": "#ff4d4d",
                    "min": {"x": 10.0, "y": 15.0, "z": 5.0},
                    "max": {"x": 35.0, "y": 40.0, "z": 12.0},
                    "center": {"x": 22.5, "y": 27.5, "z": 8.5}
                }
            },
            {
                "issue_id": "issue-002",
                "type": "deep_pocket",
                "severity": "medium",
                "message": "Pocket depth-to-width ratio of 5:1 exceeds the recommended 4:1 for standard tooling.",
                "recommendation": "Reduce pocket depth or widen the pocket opening.",
                "three_js_highlight": {
                    "type": "bounding_box",
                    "color": "#ffb84d",
                    "min": {"x": 60.0, "y": 20.0, "z": 0.0},
                    "max": {"x": 85.0, "y": 55.0, "z": 30.0},
                    "center": {"x": 72.5, "y": 37.5, "z": 15.0}
                }
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