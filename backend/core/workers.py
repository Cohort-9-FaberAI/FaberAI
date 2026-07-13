from celery import Celery
from app.database import supabase
from app.crud import insert_analysis_result
from app.schemas import AnalysisResult, AnalysisStatus
from app.services.geometry_engine_adapter import run_geometry_engine
import tempfile
import os
import requests

# Connection to Redis
REDIS_URL = "redis://localhost:6379/0"

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
)


@celery_app.task(name="extract_geometry_task")
def extract_geometry_task(file_url: str, original_filename: str):
    """
    Downloads the CAD file from Supabase Storage into a secure temporary file,
    passes the temporary path to the geometry engine, then cleans up automatically.

    Args:
        file_url: The public Supabase Storage URL of the uploaded CAD file.
        original_filename: The original name of the file for logging and context.
    """
    print(f"[WORKER] Starting processing for: {original_filename}")
    print(f"[WORKER] Downloading from: {file_url}")

    # Determine file extension from original filename
    file_extension = original_filename.split(".")[-1].lower()

    tmp_path = None
    try:
        # Download file from Supabase Storage into a secure temp file
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}",
            delete=False
        ) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        print(f"[WORKER] File downloaded to temp path: {tmp_path}")

        # Delegate analysis to the geometry engine adapter (currently a mock)
        result = run_geometry_engine(tmp_path, original_filename)
        print(f"[WORKER] Processing complete for: {original_filename}")

        # Persist the analysis so /tasks/{task_id} can fetch it from Supabase
        analysis = AnalysisResult(
            filename=original_filename,
            status=AnalysisStatus.completed,
            manufacturability_score=result["mock_score"],
        )
        insert_analysis_result(analysis)
        print(f"[WORKER] Analysis result persisted: {analysis.analysis_id}")

        # Expose analysis_id so the status endpoint can look up the record
        return {**result, "analysis_id": analysis.analysis_id}

    finally:
        # Always clean up the temp file, even if processing fails
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f"[WORKER] Temp file deleted: {tmp_path}")