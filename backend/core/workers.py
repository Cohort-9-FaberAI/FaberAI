import time
from celery import Celery

# conection to Redis
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
def extract_geometry_task(file_name: str):
    """
    Simula a extração de geometria pesada para não travar a API.
    """
    print(f"[WORKER] Arquivo recebido: {file_name}. Iniciando processamento...")
    time.sleep(5) # simulation
    print(f"[WORKER] Finalizado o processamento de {file_name}!")
    
    return {
        "status": "completed", 
        "file": file_name, 
        "mock_score": 85
    }