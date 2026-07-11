import os
import sys
from pathlib import Path

# Make backend modules (main, app/, core/) importable when running pytest
# from any directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# app.database raises EnvironmentError at import time if Supabase credentials
# are missing. Provide fake ones so the test suite never needs a real .env
# and never touches a real Supabase project. setdefault keeps real values if
# the developer has them exported.
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client():
    return TestClient(main.app)
