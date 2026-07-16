from celery import Celery
from app.database import supabase
from app.crud import insert_analysis_result, update_analysis_status
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
def extract_geometry_task(self, file_url: str, original_filename: str, analysis_id: str):
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

        # Build a complete AnalysisResult that carries the geometry payload
        # inside geometry_data so the API can round-trip it without stripping fields.
        analysis_result = AnalysisResult(
            analysis_id=analysis_id,
            filename=original_filename,
            status=AnalysisStatus.completed,
            manufacturability_score=result.get("mock_score"),
            geometry_data=result,
        )

        update_analysis_status(
            analysis_id,
            AnalysisStatus.completed.value,
            extra_fields={
                "manufacturability_score": result.get("mock_score"),
                "results_json": analysis_result.model_dump(),
            }
        )
        print(f"[WORKER] Status set to completed for: {analysis_id}")

        return {**result, "analysis_id": analysis_id}

    except Exception as exc:
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