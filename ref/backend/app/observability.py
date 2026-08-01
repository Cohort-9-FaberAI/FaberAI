"""
LangTrace observability setup for FaberAI.

This module initialises the LangTrace SDK so that all LLM calls
(Muse Spark agent, MCP tool executions, and explanation layer)
are automatically traced and visible in the LangTrace dashboard.

Usage:
    Import and call setup_langtrace() once at application startup
    (e.g. at the top of main.py or workers.py before any LLM calls).

Dashboard:
    http://localhost:3000  (when running docker-compose locally)

Environment variables required in .env:
    LANGTRACE_API_KEY   - API key generated from the LangTrace dashboard
    LANGTRACE_HOST      - defaults to http://localhost:3000
"""

import logging
import os

logger = logging.getLogger(__name__)


def setup_langtrace() -> bool:
    """
    Initialises LangTrace tracing for the current process.

    Returns True if tracing was enabled successfully, False if the SDK
    is not installed or the API key is missing (so the app still starts
    without tracing in environments where LangTrace is not configured).
    """
    api_key = os.environ.get("LANGTRACE_API_KEY", "")
    host = os.environ.get("LANGTRACE_HOST", "http://localhost:3000")

    if not api_key:
        logger.warning(
            "LANGTRACE_API_KEY is not set — LLM tracing is disabled. "
            "Generate a key at %s and add it to your .env file.",
            host,
        )
        return False

    try:
        from langtrace_python_sdk import langtrace

        langtrace.init(
            api_key=api_key,
            api_host=f"{host}/api/trace",
            # Disable telemetry back to LangTrace's own servers —
            # we are self-hosted and want all data to stay local.
            disable_instrumentations=None,
        )
        logger.info("LangTrace tracing enabled — dashboard at %s", host)
        return True

    except ImportError:
        logger.warning(
            "langtrace-python-sdk is not installed — LLM tracing is disabled. "
            "Run: pip install langtrace-python-sdk"
        )
        return False

    except Exception as exc:
        logger.error("Failed to initialise LangTrace: %s", exc, exc_info=True)
        return False