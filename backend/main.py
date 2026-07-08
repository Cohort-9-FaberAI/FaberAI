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