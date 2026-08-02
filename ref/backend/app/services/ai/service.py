"""The AI service: answers questions about a finished DFM report.

Boundaries this layer enforces:

* it **never runs the geometry engine** — it receives geometry facts, or nothing;
* it **never runs the DFM rule engine** — a request without a stored report is
  rejected rather than re-analysed;
* it answers from report data only, and degrades to deterministic templated
  answers when no LLM provider is configured or the provider call fails.

Because the verdicts are deterministic, an LLM outage downgrades prose quality
and nothing else — the facts in the answer are identical either way.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from dfm.models import DFMReport

from .client import LLMClient, LLMNotConfigured, LLMRequestError, get_llm_client
from .context_builder import build_ai_context
from .deterministic import answer_from_report, classify_intent
from .prompts import build_messages

logger = logging.getLogger(__name__)


class AnswerMode(str, Enum):
    llm = "llm"
    deterministic = "deterministic"


class AIAnswer(BaseModel):
    """Response returned by the AI endpoint."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    mode: AnswerMode
    model: Optional[str] = None
    # Rule ids the answer is grounded in, so the UI can link to those results.
    referenced_rules: List[str] = Field(default_factory=list)
    analysis_id: Optional[str] = None
    # Set when the LLM was configured but the call could not be completed.
    degraded_reason: Optional[str] = None


class AIServiceError(RuntimeError):
    """The question cannot be answered — e.g. no report exists yet."""


def answer_dfm_question(
    report: DFMReport,
    question: str,
    geometry: Optional[Dict[str, Any]] = None,
    client: Optional[LLMClient] = None,
    analysis_id: Optional[str] = None,
) -> AIAnswer:
    """Answer a question about an already-computed DFM report.

    Args:
        report: The manufacturability report. Never recomputed here.
        question: The engineer's question.
        geometry: Optional geometry payload; only aggregate facts are passed on.
        client: LLM client override (tests).
        analysis_id: Echoed back for traceability.
    """
    if not question or not question.strip():
        raise AIServiceError("A question is required.")

    # Always compute the deterministic answer: it is the fallback, and its rule
    # references ground the response whichever path produces the prose.
    fallback_answer, referenced_rules = answer_from_report(report, question)

    client = client or get_llm_client()
    if not client.is_configured:
        return AIAnswer(
            question=question,
            answer=fallback_answer,
            mode=AnswerMode.deterministic,
            referenced_rules=referenced_rules,
            analysis_id=analysis_id or report.analysis_id,
        )

    context = build_ai_context(report, geometry)
    try:
        text = client.complete(build_messages(question, context))
    except (LLMNotConfigured, LLMRequestError) as exc:
        logger.warning("AI answer degraded to deterministic mode: %s", exc)
        return AIAnswer(
            question=question,
            answer=fallback_answer,
            mode=AnswerMode.deterministic,
            referenced_rules=referenced_rules,
            analysis_id=analysis_id or report.analysis_id,
            degraded_reason=str(exc),
        )

    if not text:
        return AIAnswer(
            question=question,
            answer=fallback_answer,
            mode=AnswerMode.deterministic,
            referenced_rules=referenced_rules,
            analysis_id=analysis_id or report.analysis_id,
            degraded_reason="The model returned an empty response.",
        )

    return AIAnswer(
        question=question,
        answer=text,
        mode=AnswerMode.llm,
        model=client.model,
        referenced_rules=_rules_mentioned(text, report) or referenced_rules,
        analysis_id=analysis_id or report.analysis_id,
    )


def _rules_mentioned(text: str, report: DFMReport) -> List[str]:
    """Rule ids the generated answer actually cites, for UI cross-linking."""
    known = [
        rule.rule_id
        for process in report.processes
        for rule in process.rule_results
    ]
    upper = text.upper()
    return [rule_id for rule_id in dict.fromkeys(known) if rule_id in upper]


__all__ = [
    "AIAnswer",
    "AIServiceError",
    "AnswerMode",
    "answer_dfm_question",
    "classify_intent",
]
