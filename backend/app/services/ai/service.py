"""The AI service: answers questions about a finished DFM report.

Boundaries this layer enforces:

* it **never runs the geometry engine** — it receives geometry facts, or nothing;
* it **never runs the DFM rule engine** — a request without a stored report is
  rejected rather than re-analysed;
* it answers from report data only, and degrades to deterministic templated
  answers when no LLM provider is configured or the provider call fails.

Because the verdicts are deterministic, an LLM outage downgrades prose quality
and nothing else — the facts in the answer are identical either way.

Standards grounding: when the LLM path runs, this module also retrieves
relevant ASME excerpts (the same retrieval used by
``app.services.dfm_knowledge``) and hands them to the model as optional,
citable context, so a conclusion like "this fails M7" can be backed by the
actual clause instead of just a rule id. Retrieval is best-effort — if it
fails or Supabase/embeddings aren't configured, the answer proceeds without
excerpts rather than failing the request.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from dfm.models import DFMReport

from .client import LLMClient, LLMNotConfigured, LLMRequestError, get_llm_client
from .context_builder import build_ai_context
from .deterministic import answer_from_report, classify_intent
from .prompts import build_messages
from .mcp_moldsim import get_moldsim

logger = logging.getLogger(__name__)

# How many ASME excerpts to pull in per question. Kept small — this is
# grounding for one answer, not a knowledge-base dump like /dfm/knowledge/ask.
STANDARDS_TOP_K = 3
STANDARDS_MIN_SIMILARITY = 0.35


class AnswerMode(str, Enum):
    llm = "llm"
    deterministic = "deterministic"


class StandardExcerpt(BaseModel):
    """One ASME chunk offered to the model as grounding for this answer.

    Mirrors ``app.services.dfm_knowledge.agent.SourceChunk`` — kept as a
    separate model rather than imported, so the report agent's response
    shape doesn't depend on the knowledge-base module's internals.
    """

    source: str
    section_ref: Optional[str] = None
    page_no: Optional[int] = None
    similarity: float


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
    # ASME excerpts offered to the model for this answer (empty when
    # retrieval found nothing relevant, isn't configured, or wasn't reached
    # because the answer came from the deterministic fallback).
    standards_considered: List[StandardExcerpt] = Field(default_factory=list)


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

    retrieval_start = time.monotonic()
    excerpts = _retrieve_standards_excerpts(question, report)
    retrieval_seconds = time.monotonic() - retrieval_start

    llm_start = time.monotonic()
    try:
        text = client.complete(build_messages(question, context, excerpts))
    except (LLMNotConfigured, LLMRequestError) as exc:
        llm_seconds = time.monotonic() - llm_start
        logger.warning(
            "AI answer degraded to deterministic mode: %s "
            "(retrieval %.2fs, llm %.2fs before failing)",
            exc, retrieval_seconds, llm_seconds,
        )
        return AIAnswer(
            question=question,
            answer=fallback_answer,
            mode=AnswerMode.deterministic,
            referenced_rules=referenced_rules,
            analysis_id=analysis_id or report.analysis_id,
            degraded_reason=str(exc),
        )
    llm_seconds = time.monotonic() - llm_start

    logger.info(
        "AI answer timing — retrieval: %.2fs (%d excerpts), llm: %.2fs, total: %.2fs",
        retrieval_seconds, len(excerpts), llm_seconds, retrieval_seconds + llm_seconds,
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
        standards_considered=[
            StandardExcerpt(
                source=c["source"],
                section_ref=c.get("section_ref"),
                page_no=c.get("page_no"),
                similarity=c["similarity"],
            )
            for c in excerpts
        ],
    )


async def answer_dfm_question_async(
    report: DFMReport,
    question: str,
    geometry: Optional[Dict[str, Any]] = None,
    client: Optional[LLMClient] = None,
    analysis_id: Optional[str] = None,
) -> AIAnswer:
    if not question or not question.strip():
        raise AIServiceError("A question is required.")

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
    excerpts = _retrieve_standards_excerpts(question, report)
    messages = build_messages(question, context, excerpts)

    moldsim = get_moldsim()
    logger.info("moldsim available: %s", bool(moldsim and moldsim.is_available))

    try:
        if moldsim and moldsim.is_available:
            text = await client.complete_with_tools(messages, moldsim.tools, moldsim)
        else:
            text = client.complete(messages)
    except (LLMNotConfigured, LLMRequestError) as exc:
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
        standards_considered=[
            StandardExcerpt(
                source=c["source"],
                section_ref=c.get("section_ref"),
                page_no=c.get("page_no"),
                similarity=c["similarity"],
            )
            for c in excerpts
        ],
    )

def _retrieve_standards_excerpts(
    question: str, report: DFMReport
) -> List[Dict[str, Any]]:
    """Best-effort ASME retrieval to ground this answer, never to block it.

    Reuses ``app.services.dfm_knowledge.retrieval`` — the same similarity
    search behind ``/dfm/knowledge/ask`` — but scoped down (top 3, higher
    similarity floor) since this is a citation aid for one answer, not a
    standalone standards lookup.

    Tries the engineer's question on its own first. Blending in blocking-rule
    names was the first approach here, but it measurably hurt retrieval: e.g.
    "does a basic dimension carry a tolerance?" alone matches ASME Section
    5.1.1 at ~0.73 similarity, but padded with printing-process rule names
    (P1, P2 — about wall thickness, unrelated to GD&T) the same query drops
    below the 0.35 floor and returns nothing. So the rule-name blend is now
    only a fallback, tried when the bare question finds nothing — it still
    helps the case it was written for (e.g. "why isn't this manufacturable?",
    which has no GD&T vocabulary of its own to embed against).

    Any failure here (Supabase unreachable, embeddings not configured, the
    knowledge module's dependencies missing) is swallowed and logged — a
    report answer must not fail because standards grounding did.
    """
    try:
        # Imported lazily: keeps this module importable (and the report
        # agent usable) even in environments where the knowledge-base
        # module's extra dependencies (embeddings, Supabase) aren't set up.
        from app.services.dfm_knowledge.retrieval import retrieve_relevant_chunks

        chunks = retrieve_relevant_chunks(
            question, top_k=STANDARDS_TOP_K, min_similarity=STANDARDS_MIN_SIMILARITY
        )
        if chunks:
            return chunks

        rule_names = [
            f"{r.rule_id} {r.name}"
            for p in report.processes
            for r in p.rule_results
            if r.rule_id in p.blocking_rule_ids
        ]
        if not rule_names:
            return []

        blended_query = f"{question} ({'; '.join(rule_names[:5])})"
        return retrieve_relevant_chunks(
            blended_query, top_k=STANDARDS_TOP_K, min_similarity=STANDARDS_MIN_SIMILARITY
        )
    except Exception as exc:  # noqa: BLE001 - retrieval must never break an answer
        logger.warning("Standards retrieval skipped for this answer: %s", exc)
        return []


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
    "StandardExcerpt",
    "answer_dfm_question",
    "answer_dfm_question_async",
    "classify_intent",
]