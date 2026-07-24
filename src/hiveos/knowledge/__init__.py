"""HiveOS Knowledge Service — FTS5-backed search with source tagging."""

from hiveos.knowledge.models import (
    KnowledgeDocument,
    KnowledgeResult,
    SourceInfo,
    IndexStats,
)
from hiveos.knowledge.service import KnowledgeService

__all__ = [
    "KnowledgeDocument",
    "KnowledgeResult",
    "SourceInfo",
    "IndexStats",
    "KnowledgeService",
]
