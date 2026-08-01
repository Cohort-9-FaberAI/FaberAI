"""Turns a parsed Docling document into rows for ``dfm_reference_docs``.

Chunk boundaries follow the standard's own structure rather than a fixed
token window: a new chunk starts at every numbered clause (``section_header``)
and whenever the running buffer gets too large for the embedding model's
context. Tables are never merged into surrounding prose — each becomes its
own chunk, stored both as markdown (for embedding/reading) and as the raw
grid (for exact lookups the UI might want later).

Every chunk is seeded with its clause heading, e.g. "5.4.2 Cross-Reference
of Standards\\n...", so the heading's own wording contributes to the chunk's
embedding rather than being a separate, disconnected element.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, List, Optional

from .docling_parser import iter_body_elements

# Conservative for bge-base-en-v1.5's 512-token window: ~4 chars/token, and
# we leave headroom for the query-side instruction prefix used at search time,
# the fact GD&T text (symbols/units) tokenizes worse than prose, and the flush
# check below only firing *after* an item is appended (so a single long list
# item or footnote can still push a chunk somewhat past this ceiling).
MAX_CHUNK_CHARS = 1000

# Matches the clause numbers ASME headings start with, e.g. "5.4.2", "3.1",
# "A.2". Headings without a leading number (e.g. "Section 3 Definitions")
# fall back to the full heading text as the section_ref.
_CLAUSE_NUMBER = re.compile(r"^([A-Za-z]?\d+(?:\.\d+)*)\b")


class _SectionState:
    def __init__(self) -> None:
        self.ref: Optional[str] = None
        self.title: str = ""

    def update(self, header_text: str) -> None:
        match = _CLAUSE_NUMBER.match(header_text.strip())
        self.ref = match.group(1) if match else header_text.strip()
        self.title = header_text.strip()


def chunk_document(doc: Dict[str, Any], source: str, doc_version: Optional[str]) -> List[Dict[str, Any]]:
    """Return a list of dicts matching the ``dfm_reference_docs`` columns:
    ``source, doc_version, section_ref, content_type, content, table_data,
    page_no``.
    """
    chunks: List[Dict[str, Any]] = []
    section = _SectionState()

    buffer: List[str] = []
    buffer_page: Optional[int] = None

    def flush() -> None:
        nonlocal buffer, buffer_page
        text = "\n".join(buffer).strip()
        if text:
            chunks.append(
                {
                    "source": source,
                    "doc_version": doc_version,
                    "section_ref": section.ref,
                    "content_type": "text",
                    "content": text,
                    "table_data": None,
                    "page_no": buffer_page,
                }
            )
        buffer = []
        buffer_page = None

    def seed_buffer() -> None:
        # Re-open a fresh buffer with the current heading so a chunk split
        # mid-clause (or a table interrupting it) doesn't lose its context.
        if section.title:
            buffer.append(section.title)

    for elem in iter_body_elements(doc):
        page_no = _page_of(elem)

        if elem["_kind"] == "section_header":
            flush()
            section.update(elem.get("text", ""))
            seed_buffer()
            buffer_page = page_no
            continue

        if elem["_kind"] == "table":
            flush()
            chunks.append(_table_chunk(elem, source, doc_version, section))
            seed_buffer()
            buffer_page = page_no
            continue

        # Plain text / list item / formula / caption.
        text = (elem.get("text") or "").strip()
        if not text:
            continue
        if buffer_page is None:
            buffer_page = page_no
        buffer.append(text)

        if sum(len(b) for b in buffer) > MAX_CHUNK_CHARS:
            flush()
            seed_buffer()
            buffer_page = page_no

    flush()
    return chunks


def _page_of(elem: Dict[str, Any]) -> Optional[int]:
    prov = elem.get("prov") or []
    return prov[0]["page_no"] if prov else None


def _table_chunk(
    table_elem: Dict[str, Any],
    source: str,
    doc_version: Optional[str],
    section: _SectionState,
) -> Dict[str, Any]:
    grid: List[List[Dict[str, Any]]] = table_elem.get("data", {}).get("grid", [])
    rows = [[cell.get("text", "").strip() for cell in row] for row in grid]

    markdown = _grid_to_markdown(rows)
    # Prefix with the clause heading so the table's embedding carries the
    # same topical context a human reader would infer from its position.
    content = f"{section.title}\n{markdown}" if section.title else markdown

    return {
        "source": source,
        "doc_version": doc_version,
        "section_ref": section.ref,
        "content_type": "table",
        "content": content,
        "table_data": rows,
        "page_no": _page_of(table_elem),
    }


def _grid_to_markdown(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(row) + " |" for row in rows]
    header_sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
    return "\n".join([lines[0], header_sep, *lines[1:]])


def iter_chunk_previews(chunks: List[Dict[str, Any]]) -> Iterator[str]:
    """Short human-readable previews — used by the ingest script's dry run."""
    for c in chunks:
        preview = c["content"][:80].replace("\n", " ")
        yield f"[{c['section_ref'] or '-'} | p.{c['page_no']} | {c['content_type']}] {preview}"