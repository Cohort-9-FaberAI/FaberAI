"""Local embedding model for the DFM knowledge base.

Uses ``BAAI/bge-base-en-v1.5`` via ``sentence-transformers``: free, runs on
CPU, and — among free local models — sits at or near the top of the MTEB
retrieval leaderboard for its size, well ahead of smaller models like
``all-MiniLM-L6-v2``. No API key, no per-call cost.

BGE models were trained with an asymmetric convention: passages (the chunks
we store) are embedded as-is, but *queries* need an instruction prefix
prepended, or retrieval quality drops noticeably. That asymmetry is handled
here so callers never have to remember it — ``embed_passages`` and
``embed_query`` are deliberately separate functions, not one with a flag.

    FABERAI_EMBEDDING_MODEL   model id (default: BAAI/bge-base-en-v1.5)

The embedding dimension for the default model is 768 — this must match the
``vector`` column width in the ``dfm_reference_docs`` migration.
"""

from __future__ import annotations

import os
from typing import List, Optional

DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768

# BGE's documented query-side instruction. Only used for search queries —
# never prepended to stored passages.
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model = None  # lazy singleton; loading pulls ~440MB the first time


def _get_model():
    global _model
    if _model is None:
        # Imported lazily: sentence-transformers/torch are only needed by the
        # ingest script and the knowledge-agent request path, not by every
        # process that imports app.services.dfm_knowledge.
        from sentence_transformers import SentenceTransformer

        model_name = os.environ.get("FABERAI_EMBEDDING_MODEL", DEFAULT_MODEL)
        _model = SentenceTransformer(model_name)
    return _model


def embed_passages(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed chunk contents for storage. No instruction prefix."""
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,  # cosine similarity assumes unit vectors
        show_progress_bar=len(texts) > batch_size,
    )
    return vectors.tolist()


def embed_query(text: str) -> List[float]:
    """Embed a search query. Prepends BGE's required query instruction."""
    model = _get_model()
    vector = model.encode(
        _QUERY_PREFIX + text,
        normalize_embeddings=True,
    )
    return vector.tolist()


def reset_model() -> None:
    """Drop the cached model (tests, or switching FABERAI_EMBEDDING_MODEL)."""
    global _model
    _model = None