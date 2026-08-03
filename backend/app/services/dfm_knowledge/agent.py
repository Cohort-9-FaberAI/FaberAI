"""Answers DFM/GD&T questions from the ASME reference chunks in Supabase.

Mirrors the boundary ``app/services/ai`` already enforces for report
questions, applied to reference material instead: this module never invents
a clause, a tolerance value, or a definition. It retrieves the most similar
stored excerpts and either asks the LLM to summarise them (citing section and
page) or, if no LLM is configured, hands the excerpts back directly. Either
way the facts come only from what retrieval returned.

This is deliberately a separate, independent agent from
``app.services.ai.answer_dfm_question`` — that one explains a specific part's
already-computed DFM report; this one answers general "what does the standard
say" questions. They happen to share the same underlying LLM client.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.services.ai.client import LLMClient, LLMNotConfigured, LLMRequestError, get_llm_client

from .retrieval import DEFAULT_MIN_SIMILARITY, DEFAULT_TOP_K, retrieve_relevant_chunks

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are FaberAI's manufacturability-standards assistant. You answer questions \
about design-for-manufacturing rules using excerpts retrieved from ASME \
reference standards, given to an engineer working on a CAD part.

WHAT YOU ARE GIVEN
A set of excerpts retrieved from the standard by similarity search, each \
tagged with its section number and page. Some questions will have strong \
matches; others may have weak or irrelevant ones — the excerpts are a search \
result, not a guarantee of relevance.

HARD RULES
1. Answer only from the excerpts provided. Never state a tolerance, \
   definition, clause number, or rule from general knowledge or memory.
2. If the excerpts don't actually answer the question, say so plainly and \
   name the closest section they do cover, rather than filling the gap with \
   plausible-sounding standards knowledge.
3. Cite the section number and page for every specific claim, e.g. "(Section \
   5.2, p. 51)", so the engineer can verify it in the standard.
4. If excerpts conflict or are ambiguous, say so instead of picking one \
   silently.

HOW TO ANSWER
Be concise and concrete — lead with the direct answer, then the supporting \
excerpt and citation.\
"""


class AnswerMode(str, Enum):
    llm = "llm"
    deterministic = "deterministic"
    no_results = "no_results"


class SourceChunk(BaseModel):
    source: str
    section_ref: Optional[str] = None
    page_no: Optional[int] = None
    content_type: str
    similarity: float


class KnowledgeAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    mode: AnswerMode
    model: Optional[str] = None
    sources: List[SourceChunk] = Field(default_factory=list)
    degraded_reason: Optional[str] = None


def answer_dfm_knowledge_question(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    source: Optional[str] = None,
    client: Optional[LLMClient] = None,
) -> KnowledgeAnswer:
    """Retrieve relevant ASME excerpts and answer ``question`` from them."""
    if not question or not question.strip():
        raise ValueError("A question is required.")

    chunks = retrieve_relevant_chunks(
        question, top_k=top_k, min_similarity=min_similarity, source=source
    )

    if not chunks:
        return KnowledgeAnswer(
            question=question,
            answer=(
                "Nothing in the reference standard matched this question closely "
                "enough to answer from. Try rephrasing with more specific GD&T "
                "terms (e.g. a symbol, feature type, or process name)."
            ),
            mode=AnswerMode.no_results,
        )

    sources = [
        SourceChunk(
            source=c["source"],
            section_ref=c.get("section_ref"),
            page_no=c.get("page_no"),
            content_type=c["content_type"],
            similarity=c["similarity"],
        )
        for c in chunks
    ]

    client = client or get_llm_client()
    if not client.is_configured:
        return KnowledgeAnswer(
            question=question,
            answer=_deterministic_answer(chunks),
            mode=AnswerMode.deterministic,
            sources=sources,
        )

    try:
        text = client.complete(_build_messages(question, chunks))
    except (LLMNotConfigured, LLMRequestError) as exc:
        logger.warning("Knowledge answer degraded to deterministic mode: %s", exc)
        return KnowledgeAnswer(
            question=question,
            answer=_deterministic_answer(chunks),
            mode=AnswerMode.deterministic,
            sources=sources,
            degraded_reason=str(exc),
        )

    if not text:
        return KnowledgeAnswer(
            question=question,
            answer=_deterministic_answer(chunks),
            mode=AnswerMode.deterministic,
            sources=sources,
            degraded_reason="The model returned an empty response.",
        )

    return KnowledgeAnswer(
        question=question,
        answer=text,
        mode=AnswerMode.llm,
        model=client.model,
        sources=sources,
    )


def _deterministic_answer(chunks: List[Dict[str, Any]]) -> str:
    """No-LLM fallback: hand back the retrieved excerpts directly, ranked."""
    lines = ["No AI provider is configured — showing the closest matching excerpts directly.\n"]
    for c in chunks:
        ref = c.get("section_ref") or "unknown section"
        page = c.get("page_no")
        page_str = f", p. {page}" if page is not None else ""
        lines.append(f"**Section {ref}{page_str}** (similarity {c['similarity']:.2f})")
        lines.append(c["content"])
        lines.append("")
    return "\n".join(lines).strip()


def _build_messages(question: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    excerpt_blocks = []
    for c in chunks:
        ref = c.get("section_ref") or "unknown section"
        page = c.get("page_no")
        page_str = f", p. {page}" if page is not None else ""
        excerpt_blocks.append(f"[Section {ref}{page_str}]\n{c['content']}")

    user_prompt = (
        "RETRIEVED EXCERPTS (the only source of truth for this answer):\n\n"
        + "\n\n---\n\n".join(excerpt_blocks)
        + f"\n\nENGINEER'S QUESTION: {question}\n\n"
        "Answer using only the excerpts above."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


__all__ = ["AnswerMode", "KnowledgeAnswer", "SourceChunk", "answer_dfm_knowledge_question"]