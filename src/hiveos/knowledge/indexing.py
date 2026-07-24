"""Indexing pipeline — parse markdown, chunk, tag."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from hiveos.knowledge.models import KnowledgeDocument


# ---------------------------------------------------------------------------
# YAML frontmatter extraction
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter(content: str) -> Tuple[dict, str]:
    """Return (frontmatter_dict, body_without_frontmatter).

    If no frontmatter, returns ({}, original_content).
    """
    m = _FRONT_MATTER_RE.match(content)
    if not m:
        return {}, content

    import yaml

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}

    return fm, content[m.end():]


# ---------------------------------------------------------------------------
# Tag generation from markdown headers
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)", re.MULTILINE)


def auto_tags_from_content(content: str) -> List[str]:
    """Extract headings from markdown and return lowercase slugs as tags."""
    tags: List[str] = []
    for m in _HEADING_RE.finditer(content):
        tag = m.group(1).strip().lower()
        tag = re.sub(r"[^a-z0-9\-_]+", "-", tag)
        tag = re.sub(r"-{2,}", "-", tag).strip("-")
        if tag and tag not in tags:
            tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Document parsing
# ---------------------------------------------------------------------------

def parse_markdown_file(
    file_path: Path,
    source_type: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[KnowledgeDocument]:
    """Parse a Markdown file into a list of KnowledgeDocuments (one per chunk)."""
    raw = file_path.read_text(encoding="utf-8")
    fm, body = extract_frontmatter(raw)
    title = fm.get("title", file_path.stem)

    tags: List[str] = []
    if "tags" in fm and isinstance(fm["tags"], list):
        tags = [str(t) for t in fm["tags"]]
    if not tags:
        tags = auto_tags_from_content(body)

    chunks = _chunk_text(body, chunk_size, chunk_overlap)
    now = datetime.now(timezone.utc)
    source_path = str(file_path)

    docs: List[KnowledgeDocument] = []
    for i, chunk_text in enumerate(chunks):
        doc = KnowledgeDocument(
            id=str(uuid.uuid4()),
            source_type=source_type,
            source_path=source_path,
            title=title,
            content=chunk_text,
            tags=tags,
            chunk_id=i,
            created_at=now,
        )
        docs.append(doc)

    # Handle empty files — produce one empty chunk so the document exists
    if not docs:
        docs.append(
            KnowledgeDocument(
                id=str(uuid.uuid4()),
                source_type=source_type,
                source_path=source_path,
                title=title,
                content=body,
                tags=tags,
                chunk_id=0,
                created_at=now,
            )
        )

    return docs


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split *text* into overlapping chunks of ~chunk_size characters."""
    if not text or not text.strip():
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap

    return chunks if chunks else [text]
