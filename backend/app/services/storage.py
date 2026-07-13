import uuid
from fastapi import UploadFile
from app.database import supabase

BUCKET_NAME = "cad-uploads"


def upload_cad_file_to_storage(file: UploadFile) -> dict:
    """
    Uploads a CAD file (STEP or STL) to Supabase Storage.

    Generates a unique storage path to prevent filename collisions.
    Returns the storage path and the public URL of the uploaded file.
    """
    file_extension = file.filename.split(".")[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    storage_path = f"uploads/{unique_filename}"

    file_bytes = file.file.read()

    supabase.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": file.content_type or "application/octet-stream"},
    )

    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)

    return {
        "storage_path": storage_path,
        "public_url": public_url,
        "original_filename": file.filename,
    }