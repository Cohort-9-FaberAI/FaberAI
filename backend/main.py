from uuid import UUID

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, UploadFile, status
from pydantic import ValidationError

from core.database import fetch_analysis_by_task_id
from core.schemas import AnalysisResult
from core.workers import celery_app, extract_geometry_task

app = FastAPI(
    title="FaberAI Backend",
    description="AI-powered manufacturability review API for CAD parts.",
    version="0.1.0",
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
    file_name = file.filename
    
    # Dispara a tarefa assíncrona
    task = extract_geometry_task.delay(file_name)
    
    return {
        "message": "File received successfully. Processing started in background.",
        "task_id": task.id,
        "filename": file_name,
        "status": "processing"
    }

@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task_status(task_id: str):
    """
    Polls the status of a background processing task.

    Returns the current Celery state (PENDING, PROCESSING, SUCCESS, FAILURE).
    On SUCCESS, fetches the final analysis from Supabase, validates it
    against the agreed API contract and returns it to the frontend.

    Note: Celery reports unknown task ids as PENDING, so a well-formed but
    nonexistent id is indistinguishable from a queued task. Malformed ids
    (not a UUID) return 404.
    """
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    result = AsyncResult(task_id, app=celery_app)

    if result.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(result.result),
        }

    if result.state == "SUCCESS":
        analysis = fetch_analysis_by_task_id(task_id)
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{task_id}' completed but no analysis was found for it.",
            )
        try:
            validated = AnalysisResult.model_validate(analysis)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stored analysis for task '{task_id}' failed validation: {exc.error_count()} error(s).",
            )
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": validated.model_dump(),
        }

    # PENDING or any other intermediate state
    return {"task_id": task_id, "status": result.state}


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