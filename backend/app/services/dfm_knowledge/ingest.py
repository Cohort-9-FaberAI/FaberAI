"""One-off ingestion of a Docling-parsed standard into dfm_reference_docs.

Run manually whenever a reference document is added or re-exported from
Docling — this is not wired into the API or the Celery pipeline, since it's
triggered by an engineer adding a document, not by end-user traffic.

Idempotent by ``source``: reruns delete-then-reinsert rather than duplicate,
so re-ingesting after fixing a docling export or bumping the chunker is safe.

Usage:
    cd backend
    python -m app.services.dfm_knowledge.ingest \\
        --file /path/to/asme_y14-5.json \\
        --source "ASME Y14.5-2018" \\
        --doc-version "2018 (R2024)"

    # Preview chunking without embedding or writing to Supabase:
    python -m app.services.dfm_knowledge.ingest --file ... --dry-run

Requires the same SUPABASE_URL / SUPABASE_KEY env vars as the rest of the
backend (see app/database.py), plus `pip install sentence-transformers`
(intentionally not in requirements.txt — see that file's comment — since it
pulls in torch and only this script and the knowledge-agent request path
need it).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

TABLE_NAME = "dfm_reference_docs"
UPLOAD_BATCH_SIZE = 200


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="Path to the Docling JSON export.")
    parser.add_argument(
        "--source", required=True,
        help='Short label stored per row, e.g. "ASME Y14.5-2018". Reingesting '
             "the same source deletes and replaces its existing rows.",
    )
    parser.add_argument("--doc-version", default=None, help='e.g. "2018 (R2024)"')
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chunk and print a preview only — no embedding, no Supabase writes.",
    )
    return parser.parse_args(argv)


def run(argv: List[str]) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args(argv)

    from .chunker import chunk_document, iter_chunk_previews

    with open(args.file, encoding="utf-8") as f:
        doc = json.load(f)

    chunks = chunk_document(doc, source=args.source, doc_version=args.doc_version)
    logger.info(
        "Chunked '%s' into %d rows (%d text, %d table).",
        args.file,
        len(chunks),
        sum(1 for c in chunks if c["content_type"] == "text"),
        sum(1 for c in chunks if c["content_type"] == "table"),
    )

    if args.dry_run:
        for preview in list(iter_chunk_previews(chunks))[:30]:
            print(preview)
        if len(chunks) > 30:
            print(f"... and {len(chunks) - 30} more")
        return

    _embed_and_upload(chunks, source=args.source)


def _embed_and_upload(chunks: List[Dict[str, Any]], source: str) -> None:
    from .embeddings import embed_passages
    from app.database import supabase

    logger.info("Embedding %d chunks with BAAI/bge-base-en-v1.5 (first run downloads the model)...", len(chunks))
    contents = [c["content"] for c in chunks]
    vectors = embed_passages(contents)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector

    logger.info("Deleting any existing rows for source='%s'...", source)
    supabase.table(TABLE_NAME).delete().eq("source", source).execute()

    logger.info("Inserting %d rows in batches of %d...", len(chunks), UPLOAD_BATCH_SIZE)
    for start in range(0, len(chunks), UPLOAD_BATCH_SIZE):
        batch = chunks[start:start + UPLOAD_BATCH_SIZE]
        supabase.table(TABLE_NAME).insert(batch).execute()
        logger.info("  inserted %d/%d", min(start + UPLOAD_BATCH_SIZE, len(chunks)), len(chunks))

    logger.info("Done. %d rows now stored for source='%s'.", len(chunks), source)


if __name__ == "__main__":
    run(sys.argv[1:])