"""Anthropic Claude client for the DFM assistant.

Talks to the Claude Messages API (``POST /v1/messages``) through the official
``anthropic`` SDK, configured entirely through environment variables so the
model can be swapped without a code change.

    FABERAI_AI_API_KEY    Claude API key (falls back to ANTHROPIC_API_KEY)
    FABERAI_AI_MODEL      model id (default: claude-opus-5)
    FABERAI_AI_BASE_URL   optional API base URL override (gateway/proxy)
    FABERAI_AI_TIMEOUT    request timeout in seconds (default: 90)
    FABERAI_AI_MAX_TOKENS response cap (default: 2000)
    FABERAI_AI_EFFORT     low | medium | high | xhigh | max (default: low)

When no key is configured the client raises ``LLMNotConfigured`` and the service
layer answers deterministically from the report instead. The endpoint stays
useful with no provider account attached.

Two Claude-specific details this module exists to get right:

* the Messages API takes the system prompt as a **top-level** parameter, not as
  a ``system`` entry in ``messages`` — ``complete()`` splits the message list
  the prompt builder produces;
* on Claude Opus 5 thinking is on by default and ``max_tokens`` caps thinking
  *plus* answer text, so the cap is sized with headroom and depth is controlled
  with ``effort`` rather than a sampling temperature (which the model rejects).
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional
from app.services.ai.mcp_moldsim import MoldSimMCP

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_TOKENS = 2000
DEFAULT_EFFORT = "low"


class LLMNotConfigured(RuntimeError):
    """No provider credentials are present in the environment."""


class LLMRequestError(RuntimeError):
    """The provider was reachable but the call failed."""


class LLMClient:
    """Minimal Messages API client — one call, no streaming, no retries.

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
        effort: Optional[str] = None,
    ):
        # Optional: only set for a gateway in front of the Claude API. Empty
        # means "use the SDK default endpoint".
        self.base_url = (base_url or os.environ.get("FABERAI_AI_BASE_URL") or "").rstrip("/")
        # ANTHROPIC_API_KEY is the name the Claude SDK and every Anthropic doc
        # uses; accept it so a standard .env works without a rename.
        self.api_key = (
            api_key
            or os.environ.get("FABERAI_AI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self.model = model or os.environ.get("FABERAI_AI_MODEL", DEFAULT_MODEL)
        self.timeout = float(
            timeout or os.environ.get("FABERAI_AI_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)
        )
        self.max_tokens = int(
            max_tokens or os.environ.get("FABERAI_AI_MAX_TOKENS", DEFAULT_MAX_TOKENS)
        )
        self.effort = effort or os.environ.get("FABERAI_AI_EFFORT", DEFAULT_EFFORT)
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _sdk(self) -> anthropic.Anthropic:
        if self._client is None:
            kwargs = {"api_key": self.api_key, "timeout": self.timeout, "max_retries": 0}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """Send a Messages API request and return the assistant's text."""
        if not self.is_configured:
            raise LLMNotConfigured(
                "No LLM provider configured. Set FABERAI_AI_API_KEY (or ANTHROPIC_API_KEY) "
                "to enable generated explanations."
            )

        # The prompt builder emits an OpenAI-style [system, user] list; the
        # Claude Messages API wants the system prompt hoisted out.
        system = "\n\n".join(
            str(m.get("content", "")) for m in messages if m.get("role") == "system"
        )
        turns = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("role") != "system"
        ]
        if not turns:
            raise LLMRequestError("No user message to send.")

        try:
            response = self._sdk().messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system or anthropic.NOT_GIVEN,
                messages=turns,
                # Depth, not randomness: Opus 5 rejects `temperature`, and the
                # same report should produce the same explanation. DFM answers
                # that drift destroy trust.
                output_config={"effort": self.effort},
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"LLM request failed: {exc}") from exc

        # Safety classifiers can decline with HTTP 200 and empty content; treat
        # that as a failed call so the deterministic answer is served instead.
        if response.stop_reason == "refusal":
            raise LLMRequestError("The model declined to answer this request.")
        if response.stop_reason == "max_tokens":
            logger.warning(
                "AI answer hit max_tokens (%s); raise FABERAI_AI_MAX_TOKENS.",
                self.max_tokens,
            )

        text = "\n".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            raise LLMRequestError(
                f"LLM returned no text content (stop_reason={response.stop_reason!r})."
            )
        return text

    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        moldsim: "MoldSimMCP",
    ) -> str:
        if not self.is_configured:
            raise LLMNotConfigured("No LLM provider configured.")

        system = "\n\n".join(
            str(m.get("content", "")) for m in messages if m.get("role") == "system"
        )
        turns = [
            {"role": m["role"], "content": m["content"]}
            for m in messages if m.get("role") != "system"
        ]
        if not turns:
            raise LLMRequestError("No user message to send.")

        claude_tools = [
            {"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
            for t in tools
        ]

        for _ in range(5):  # hard cap on tool-call rounds — same "no retries at cost" spirit as complete()
            try:
                response = self._sdk().messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system or anthropic.NOT_GIVEN,
                    messages=turns,
                    tools=claude_tools,
                    output_config={"effort": self.effort},
                )
            except anthropic.APIError as exc:
                raise LLMRequestError(f"LLM request failed: {exc}") from exc

            if response.stop_reason == "refusal":
                raise LLMRequestError("The model declined to answer this request.")

            if response.stop_reason != "tool_use":
                text = "\n".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                ).strip()
                if not text:
                    raise LLMRequestError(f"LLM returned no text (stop_reason={response.stop_reason!r}).")
                return text

            turns.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    try:
                        result = await moldsim.session.call_tool(block.name, block.input)
                        content = result.content
                    except Exception as exc:
                        content = [{"type": "text", "text": f"Tool error: {exc}"}]
                    tool_results.append({
                        "type": "tool_result", "tool_use_id": block.id, "content": content,
                    })
            turns.append({"role": "user", "content": tool_results})

        raise LLMRequestError("Exceeded tool-call round limit.")


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
