"""RAG layer over reference standards (currently: ASME Y14.5) for DFM Q&A.

Ingestion (offline, manual): docling_parser + chunker turn a Docling JSON
export into rows for the `dfm_reference_docs` Supabase table; embeddings.py
embeds them; ingest.py is the CLI entry point that ties those together and
writes to Supabase.

Serving (online, per-request): retrieval.py does similarity search;
agent.py answers a question from what retrieval returns, via the same
LLMClient the DFM-report assistant uses.
"""

from .agent import AnswerMode, KnowledgeAnswer, SourceChunk, answer_dfm_knowledge_question
from .retrieval import retrieve_relevant_chunks

__all__ = [
    "AnswerMode",
    "KnowledgeAnswer",
    "SourceChunk",
    "answer_dfm_knowledge_question",
    "retrieve_relevant_chunks",
]