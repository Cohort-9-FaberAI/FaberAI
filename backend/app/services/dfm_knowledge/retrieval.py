"""Similarity search over dfm_reference_docs.

Thin by design: embed the query, call the ``match_dfm_reference_docs`` RPC
(defined in database/migrations/02_dfm_reference_docs_vector_search.sql), and
return the rows as-is. No re-ranking, no query rewriting — the agent module
decides what to do with what comes back.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .embeddings import embed_query

DEFAULT_TOP_K = 5
DEFAULT_MIN_SIMILARITY = 0.3


def retrieve_relevant_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return up to ``top_k`` chunks most similar to ``query``.

    Each result dict has: id, source, doc_version, section_ref, content_type,
    content, table_data, page_no, similarity.
    """
    if not query or not query.strip():
        return []

    # Imported lazily so modules that only need chunking (e.g. ingest.py
    # --dry-run) don't require Supabase credentials just to be imported.
    from app.database import supabase

    query_vector = embed_query(query)
    response = supabase.rpc(
        "match_dfm_reference_docs",
        {
            "query_embedding": query_vector,
            "match_count": top_k,
            "min_similarity": min_similarity,
            "filter_source": source,
        },
    ).execute()
    return response.data or []