import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
STORAGE_BACKEND = os.environ.get("FABERAI_STORAGE_BACKEND", "supabase").lower()
if STORAGE_BACKEND not in {"local", "supabase"}:
    raise EnvironmentError("FABERAI_STORAGE_BACKEND must be 'local' or 'supabase'.")
LOCAL_MODE = STORAGE_BACKEND == "local"

if not LOCAL_MODE and (not SUPABASE_URL or not SUPABASE_KEY):
    raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_KEY must be set in your .env file. "
        "See the root .env.example, or set FABERAI_STORAGE_BACKEND=local for development."
    )

supabase: Client | None = None if LOCAL_MODE else create_client(SUPABASE_URL, SUPABASE_KEY)
