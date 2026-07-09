from fastapi import FastAPI, UploadFile, status
from core.workers import extract_geometry_task

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