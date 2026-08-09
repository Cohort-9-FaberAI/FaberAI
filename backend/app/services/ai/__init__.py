"""AI integration layer for the DFM engine.

Consumes geometry results and the DFM report only — it never reruns geometry
analysis and never re-evaluates a DFM rule.
"""

from .client import (
    LLMClient,
    LLMNotConfigured,
    LLMRequestError,
    get_llm_client,
    reset_llm_client,
)
from .context_builder import build_ai_context, summarise_failures
from .deterministic import QuestionIntent, answer_from_report, classify_intent
from .prompts import SYSTEM_PROMPT, build_messages
from .service import (
    AIAnswer,
    AIServiceError,
    AnswerMode,
    StandardExcerpt,
    answer_dfm_question,
)

__all__ = [
    "SYSTEM_PROMPT",
    "AIAnswer",
    "AIServiceError",
    "AnswerMode",
    "LLMClient",
    "LLMNotConfigured",
    "LLMRequestError",
    "QuestionIntent",
    "StandardExcerpt",
    "answer_dfm_question",
    "answer_from_report",
    "build_ai_context",
    "build_messages",
    "classify_intent",
    "get_llm_client",
    "reset_llm_client",
    "summarise_failures",
]