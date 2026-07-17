import os
import uuid
from fastapi import HTTPException, UploadFile, status
from app.database import supabase
from geometry.loaders.dispatcher import STEP_EXTENSIONS, STL_EXTENSIONS, get_file_format

BUCKET_NAME = "cad-uploads"

# Maximum upload size, configurable via env var (whole megabytes).
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "100"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Uploads are read in chunks of this size while enforcing the limit.
UPLOAD_CHUNK_SIZE = 1024 * 1024


def validate_upload_filename(filename: str | None) -> str:
    """
    Validates an upload's filename before anything is stored or dispatched.

    Rejects missing/empty filenames, filenames without an extension, and
    extensions the geometry engine can't load (delegates to get_file_format
    so the whitelist lives in one place). Returns the normalized extension
    without the leading dot (e.g. "stl").
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    extension = os.path.splitext(filename)[1]
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must include a file extension.",
        )

    try:
        get_file_format(filename)
    except ValueError:
        supported = ", ".join(sorted(STEP_EXTENSIONS | STL_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension '{extension}'. "
                f"Supported formats: {supported}."
            ),
        )

    return extension.lstrip(".").lower()


def _read_upload_within_limit(file: UploadFile) -> bytes:
    """
    Reads the upload in chunks, aborting with 413 as soon as the configured
    size limit is exceeded so oversized files are never fully buffered.
    """
    buffer = bytearray()
    while True:
        chunk = file.file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File exceeds the maximum upload size of "
                    f"{MAX_UPLOAD_SIZE_MB} MB."
                ),
            )
    return bytes(buffer)


def upload_cad_file_to_storage(file: UploadFile) -> dict:
    """
    Uploads a CAD file (STEP or STL) to Supabase Storage.

    Validates the filename/extension and enforces the maximum upload size
    before touching Supabase, so invalid uploads fail fast with 400/413.
    Generates a unique storage path to prevent filename collisions.
    Returns the storage path and the public URL of the uploaded file.
    """
    file_extension = validate_upload_filename(file.filename)
    file_bytes = _read_upload_within_limit(file)

    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    storage_path = f"uploads/{unique_filename}"

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
