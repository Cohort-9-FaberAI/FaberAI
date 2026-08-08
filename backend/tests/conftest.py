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


@pytest.fixture(autouse=True)
def bypass_dependency_health_checks(monkeypatch):
    monkeypatch.setattr(main, "_check_analysis_queue", lambda: None)


@pytest.fixture(autouse=True)
def no_live_llm_calls(monkeypatch):
    """Keep the unit suite offline and free.

    ``app.database`` calls ``load_dotenv()`` at import time, so a developer .env
    holding a real key would otherwise put every AI test on the live Claude API:
    slow, billable, and non-deterministic. The AI benchmark under
    ``tests/ai_eval`` is the one place that is allowed to call the provider, and
    it reads the key itself rather than going through this fixture.
    """
    from app.services.ai.client import reset_llm_client

    for name in ("FABERAI_AI_API_KEY", "ANTHROPIC_API_KEY", "FABERAI_AI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    reset_llm_client()
    yield
    reset_llm_client()
