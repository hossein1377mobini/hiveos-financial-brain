"""Data models for the Knowledge Service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class KnowledgeDocument:
    """A single knowledge document (or chunk) stored in the index."""

    id: str  # UUID
    source_type: str  # "domain:<pack_id>" or "org"
    source_path: str  # Original file path
    title: str
    content: str  # Full text of this chunk
    tags: List[str] = field(default_factory=list)
    chunk_id: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class KnowledgeResult:
    """A search result returned by KnowledgeService.search."""

    doc_id: str
    source_type: str
    source_path: str
    title: str
    snippet: str  # Highlighted or truncated content
    score: float
    chunk_id: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class SourceInfo:
    """Metadata about a knowledge source (grouped by source_type)."""

    source_type: str
    document_count: int
    paths: List[str] = field(default_factory=list)


@dataclass
class IndexStats:
    """Overall statistics for the knowledge index."""

    total_documents: int
    total_chunks: int
    total_sources: int
    source_breakdown: List[SourceInfo] = field(default_factory=list)
