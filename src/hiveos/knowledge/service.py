"""KnowledgeService — facade over the FTS5 knowledge index."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from hiveos.knowledge.ingestion import (
    ensure_tables,
    ingest_single_file,
    ingest_directory as _ingest_dir,
    ingest_domain_pack as _ingest_domain,
)
from hiveos.knowledge.models import (
    KnowledgeDocument,
    KnowledgeResult,
    SourceInfo,
    IndexStats,
)
from hiveos.knowledge.search import search_fts5
from hiveos.storage import StorageEngine


class KnowledgeService:
    """Unified search index over domain and organisation knowledge."""

    def __init__(self, storage_engine: StorageEngine):
        self._engine = storage_engine
        ensure_tables(storage_engine)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        source_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[KnowledgeResult]:
        """Full-text search with optional source and tag filters."""
        return search_fts5(
            self._engine.fetch_all,
            query,
            source_filter=source_filter,
            tags=tags,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest_document(self, doc: KnowledgeDocument) -> str:
        """Insert a single KnowledgeDocument. Returns doc ID."""
        ensure_tables(self._engine)
        tags_str = ",".join(doc.tags)
        now_iso = doc.created_at.isoformat()
        with self._engine._lock:
            conn = self._engine._conn
            conn.execute(
                """INSERT INTO knowledge
                   (id, source_type, source_path, title, content, tags, chunk_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc.id, doc.source_type, doc.source_path, doc.title, doc.content,
                 tags_str, doc.chunk_id, now_iso),
            )
            conn.execute(
                """INSERT INTO knowledge_fts (rowid, title, content, tags)
                   SELECT rowid, title, content, tags FROM knowledge WHERE id = ?""",
                (doc.id,),
            )
            conn.commit()
        return doc.id

    async def ingest_directory(self, directory: str, source_type: str) -> int:
        """Ingest all markdown/txt files in a directory. Returns chunk count."""
        return _ingest_dir(self._engine, directory, source_type)

    async def ingest_domain_pack(self, pack_path: str, pack_id: str) -> int:
        """Ingest the knowledge/ dir of a Domain Pack. Returns chunk count."""
        return _ingest_domain(self._engine, pack_path, pack_id)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Fetch a single document by its UUID."""
        row = self._engine.fetch_one(
            "SELECT id, source_type, source_path, title, content, tags, chunk_id, created_at "
            "FROM knowledge WHERE id = ?",
            (doc_id,),
        )
        if not row:
            return None
        return self._row_to_doc(row)

    async def delete_document(self, doc_id: str) -> bool:
        """Remove a document from the index. Returns True if deleted."""
        row = self._engine.fetch_one(
            "SELECT rowid FROM knowledge WHERE id = ?", (doc_id,)
        )
        if not row:
            return False
        rowid = row[0]
        with self._engine._lock:
            self._engine._conn.execute(
                "DELETE FROM knowledge_fts WHERE rowid = ?", (rowid,)
            )
            self._engine._conn.execute(
                "DELETE FROM knowledge WHERE id = ?", (doc_id,)
            )
            self._engine._conn.commit()
        return True

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    async def list_sources(self) -> List[SourceInfo]:
        """List all sources (grouped by source_type)."""
        rows = self._engine.fetch_all(
            "SELECT source_type, source_path, COUNT(*) as cnt FROM knowledge "
            "GROUP BY source_type, source_path ORDER BY source_type"
        )
        source_map: Dict[str, List[str]] = {}
        source_counts: Dict[str, int] = {}
        for src_type, src_path, cnt in rows:
            if src_type not in source_map:
                source_map[src_type] = []
                source_counts[src_type] = 0
            source_map[src_type].append(src_path)
            source_counts[src_type] += cnt

        return [
            SourceInfo(source_type=st, document_count=source_counts.get(st, 0), paths=path_list)
            for st, path_list in source_map.items()
        ]

    async def stats(self) -> IndexStats:
        """Return overall index statistics."""
        total = self._engine.fetch_one("SELECT COUNT(*) FROM knowledge") or (0,)
        total_chunks = total[0]

        total_docs = self._engine.fetch_one(
            "SELECT COUNT(DISTINCT source_path) FROM knowledge"
        ) or (0,)

        source_rows = self._engine.fetch_all(
            "SELECT source_type, COUNT(*) FROM knowledge GROUP BY source_type ORDER BY source_type"
        )
        breakdown = [
            SourceInfo(source_type=row[0], document_count=row[1])
            for row in source_rows
        ]

        return IndexStats(
            total_documents=total_docs[0],
            total_chunks=total_chunks,
            total_sources=len(breakdown),
            source_breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_doc(row: tuple) -> KnowledgeDocument:
        from datetime import datetime

        tag_str = row[5] if row[5] else ""
        tags = [t.strip() for t in tag_str.split(",") if t.strip()]
        created = row[7]
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        return KnowledgeDocument(
            id=row[0],
            source_type=row[1],
            source_path=row[2],
            title=row[3],
            content=row[4],
            tags=tags,
            chunk_id=row[6],
            created_at=created,
        )
