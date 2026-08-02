"""Provider-agnostic LLM client for the DFM assistant.

Talks to either an OpenAI-compatible ``/chat/completions`` endpoint or
Anthropic's native ``/v1/messages`` API, picked automatically from
``FABERAI_AI_BASE_URL`` (Anthropic is used when the base URL contains
"anthropic.com"; everything else assumes OpenAI-shaped). Configured entirely
through environment variables, so the model/provider can be swapped without a
code change. Default model: claude-opus-4-8 (team decision, updated from the
earlier muse-spark-1.1 placeholder).

    FABERAI_AI_BASE_URL   provider base URL (no trailing /chat/completions
                           or /v1/messages — that suffix is added per-provider)
    FABERAI_AI_API_KEY    bearer token / Anthropic API key; absent means
                           "AI not configured"
    FABERAI_AI_MODEL      model id (default: claude-opus-4-8)
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

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_TOKENS = 900
ANTHROPIC_API_VERSION = "2023-06-01"


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

    @property
    def is_anthropic(self) -> bool:
        """True when FABERAI_AI_BASE_URL points at Anthropic's own API.

        Anthropic's ``/v1/messages`` endpoint uses a different auth header,
        request body, and response shape than the OpenAI-style
        ``/chat/completions`` convention this client otherwise assumes — so
        this flag decides which branch ``complete()`` takes.
        """
        return "anthropic.com" in self.base_url

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat completion and return the assistant's text."""
        if not self.is_configured:
            raise LLMNotConfigured(
                "No LLM provider configured. Set FABERAI_AI_BASE_URL and FABERAI_AI_API_KEY "
                "to enable generated explanations."
            )
        if self.is_anthropic:
            return self._complete_anthropic(messages)
        return self._complete_openai(messages)

    def _complete_openai(self, messages: List[Dict[str, str]]) -> str:
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
        except requests.exceptions.RequestException as exc:
            raise LLMRequestError(f"LLM request failed: {exc}") from exc

        if not response.ok:
            raise LLMRequestError(
                f"LLM provider returned {response.status_code}: {response.text}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise LLMRequestError(f"LLM returned a non-JSON response: {exc}") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            raise LLMRequestError(
                f"Unexpected LLM response shape: {payload!r}"
            ) from exc

    def _complete_anthropic(self, messages: List[Dict[str, str]]) -> str:
        # Anthropic takes "system" as a top-level field, not a message with
        # role="system" — every caller in this codebase builds messages the
        # OpenAI way, so split it out here rather than touching every caller.
        system_prompt, chat_messages = _split_system_message(messages)
        if not chat_messages:
            raise LLMRequestError("No user/assistant messages to send (only a system message).")

        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": chat_messages,
            # No "temperature" here on purpose: newer Anthropic models (e.g.
            # claude-opus-4-8) reject it outright with a 400 "temperature is
            # deprecated for this model" error. Older models accept omitting
            # it fine too (falls back to their own default), so leaving it
            # out is the version that works across the model lineup.
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_API_VERSION,
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            raise LLMRequestError(f"LLM request failed: {exc}") from exc

        if not response.ok:
            # requests' raise_for_status() only gives "400 Bad Request" — the
            # useful part is Anthropic's own error body, e.g. {"error":
            # {"type": "invalid_request_error", "message": "model: ... "}}.
            raise LLMRequestError(
                f"Anthropic API returned {response.status_code}: {response.text}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise LLMRequestError(f"LLM returned a non-JSON response: {exc}") from exc

        try:
            blocks = payload["content"]
            text = "".join(b["text"] for b in blocks if b.get("type") == "text")
            if not text:
                raise KeyError("no text content blocks")
            return text.strip()
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            raise LLMRequestError(
                f"Unexpected LLM response shape: {payload!r}"
            ) from exc


def _split_system_message(
    messages: List[Dict[str, str]]
) -> tuple[Optional[str], List[Dict[str, str]]]:
    """Pull out role="system" messages (Anthropic wants them separately).

    Concatenates multiple system messages if present, in order. Everything
    else passes through unchanged and in order.
    """
    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    chat_messages = [m for m in messages if m.get("role") != "system"]
    system_prompt = "\n\n".join(system_parts) if system_parts else None
    return system_prompt, chat_messages


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