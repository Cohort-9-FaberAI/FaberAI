"""Persistent, shared development storage without a Supabase account."""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote, urlsplit


def data_dir() -> Path:
    return Path(os.environ.get("FABERAI_DATA_DIR", Path(__file__).resolve().parents[2] / ".data"))


def files_dir() -> Path:
    directory = data_dir() / "files"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def public_base_url() -> str:
    return os.environ.get("FABERAI_PUBLIC_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _file_path(storage_path: str) -> Path:
    if "\\" in storage_path or ":" in storage_path or storage_path.startswith("/"):
        raise ValueError("File path must be a relative storage path.")
    root = files_dir().resolve()
    target = (root / storage_path).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("File path must stay inside local file storage.")
    return target


def save_file(storage_path: str, content: bytes) -> str:
    target = _file_path(storage_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{uuid.uuid4()}.tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return f"{public_base_url()}/files/{storage_path}"


def read_file_url(url: str) -> bytes:
    """Read the shared volume directly; browser localhost is not worker localhost."""
    parsed = urlsplit(url)
    base = urlsplit(f"{public_base_url()}/files/")
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        raise ValueError("URL does not belong to this local file store.")
    if not parsed.path.startswith(base.path):
        raise ValueError("URL does not point to a stored file.")
    return _file_path(unquote(parsed.path[len(base.path):])).read_bytes()


@contextmanager
def _connection():
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(directory / "analyses.sqlite3", timeout=30)
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS analysis_jobs "
            "(analysis_id TEXT PRIMARY KEY, record TEXT NOT NULL)"
        )
        with connection:
            yield connection
    finally:
        connection.close()


def insert_record(record: dict) -> list[dict]:
    with _connection() as connection:
        connection.execute(
            "INSERT INTO analysis_jobs (analysis_id, record) VALUES (?, ?)",
            (record["analysis_id"], json.dumps(record)),
        )
    return [record]


def get_record(analysis_id: str) -> dict | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT record FROM analysis_jobs WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def update_record(analysis_id: str, payload: dict) -> list[dict]:
    with _connection() as connection:
        # Serialize read/modify/write across the API and Celery processes.
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT record FROM analysis_jobs WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
        if row is None:
            return []
        record = {**json.loads(row[0]), **payload}
        connection.execute(
            "UPDATE analysis_jobs SET record = ? WHERE analysis_id = ?",
            (json.dumps(record), analysis_id),
        )
    return [record]
