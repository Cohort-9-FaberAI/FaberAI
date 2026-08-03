"""Provider-agnostic LLM client for the DFM assistant.

Talks to any OpenAI-compatible ``/chat/completions`` endpoint, configured
entirely through environment variables, so the model can be swapped without a
code change. Defaults follow the team's LLM selection analysis: Muse Spark 1.1
primary (cheapest tool-calling-grade model, lowest hallucination rate of the
viable candidates), with a faster-TTFT model kept as the interactive fallback.

    FABERAI_AI_BASE_URL   provider base URL (no trailing /chat/completions)
    FABERAI_AI_API_KEY    bearer token; absent means "AI not configured"
    FABERAI_AI_MODEL      model id (default: muse-spark-1.1)
    FABERAI_AI_TIMEOUT    request timeout in seconds (default: 90)
    FABERAI_AI_MAX_TOKENS response cap (default: 900)

When no key is configured the client raises ``LLMNotConfigured`` and the service
layer answers deterministically from the report instead. The endpoint stays
useful with no provider account attached.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "muse-spark-1.1"
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_TOKENS = 900


class LLMNotConfigured(RuntimeError):
    """No provider credentials are present in the environment."""


class LLMRequestError(RuntimeError):
    """The provider was reachable but the call failed."""


class LLMClient:
    """Minimal chat-completions client — one call, no streaming, no retries.

    Deliberately thin: the DFM verdicts are deterministic, so the model is only
    writing explanation text. A failed call degrades to the deterministic
    answerer rather than being retried at cost.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.base_url = (base_url or os.environ.get("FABERAI_AI_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("FABERAI_AI_API_KEY", "")
        self.model = model or os.environ.get("FABERAI_AI_MODEL", DEFAULT_MODEL)
        self.timeout = float(
            timeout or os.environ.get("FABERAI_AI_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)
        )
        self.max_tokens = int(
            max_tokens or os.environ.get("FABERAI_AI_MAX_TOKENS", DEFAULT_MAX_TOKENS)
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat completion and return the assistant's text."""
        if not self.is_configured:
            raise LLMNotConfigured(
                "No LLM provider configured. Set FABERAI_AI_BASE_URL and FABERAI_AI_API_KEY "
                "to enable generated explanations."
            )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    # Low temperature: the same report should produce the same
                    # explanation. DFM answers that drift destroy trust.
                    "temperature": 0.1,
                    "max_tokens": self.max_tokens,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            raise LLMRequestError(f"LLM request failed: {exc}") from exc
        except ValueError as exc:
            raise LLMRequestError(f"LLM returned a non-JSON response: {exc}") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            raise LLMRequestError(
                f"Unexpected LLM response shape: {payload!r}"
            ) from exc


_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Process-wide client. Re-read config with ``reset_llm_client()``."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


def reset_llm_client() -> None:
    """Drop the cached client so new environment values take effect (tests)."""
    global _default_client
    _default_client = None
