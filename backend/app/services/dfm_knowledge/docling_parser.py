from __future__ import annotations

from typing import Any, Dict, Iterator

# Docling marks running headers/footers (repeated on every page) with this
# content layer. They add noise, not DFM knowledge, so the chunker drops them.
FURNITURE_LAYER = "furniture"

# Table-of-contents tables. Real technical tables use "table".
_TOC_TABLE_LABEL = "document_index"


def _resolve(ref: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    """``"#/texts/417"`` -> ``doc["texts"][417]``."""
    _, collection, index = ref.split("/")
    return doc[collection][int(index)]


def iter_body_elements(doc: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Yield every meaningful element in the document's reading order.

    Each yielded dict is the raw Docling element (a ``texts[i]`` or
    ``tables[i]`` entry) plus a ``_kind`` key set to one of:
    ``"section_header"``, ``"text"``, ``"table"``.

    Furniture (page headers/footers) and pictures are dropped, except that a
    picture's caption (if any) is yielded as a plain text element — captions
    like "Figure 3-1 Related and Unrelated AME" carry real information even
    though the image itself can't be embedded.
    """
    yield from _walk(doc["body"]["children"], doc)


def _walk(children: list, doc: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    for child_ref in children:
        elem = _resolve(child_ref["$ref"], doc)
        collection = child_ref["$ref"].split("/")[1]

        if collection == "groups":
            # Groups (e.g. bullet lists) have no content of their own —
            # descend into their children in order.
            yield from _walk(elem.get("children", []), doc)
            continue

        if collection == "pictures":
            for caption_ref in elem.get("captions", []):
                caption = _resolve(caption_ref["$ref"], doc)
                if caption.get("content_layer") != FURNITURE_LAYER:
                    yield {**caption, "_kind": "text"}
            continue

        if collection == "tables":
            if elem.get("label") == _TOC_TABLE_LABEL:
                continue
            yield {**elem, "_kind": "table"}
            continue

        # collection == "texts"
        if elem.get("content_layer") == FURNITURE_LAYER:
            continue
        label = elem.get("label")
        if label == "section_header":
            yield {**elem, "_kind": "section_header"}
        elif label in ("text", "list_item", "formula", "caption"):
            yield {**elem, "_kind": "text"}
        # Anything else (e.g. empty formula placeholders with no text) is
        # skipped — it has nothing to embed.