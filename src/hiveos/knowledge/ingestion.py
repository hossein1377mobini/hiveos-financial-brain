"""Ingestion — load files and Domain Pack knowledge into the index."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from hiveos.knowledge.models import KnowledgeDocument
from hiveos.knowledge.indexing import parse_markdown_file
from hiveos.storage import StorageEngine


# ---------------------------------------------------------------------------
# Table setup
# ---------------------------------------------------------------------------

_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title,
    content,
    tags,
    content=knowledge,
    content_rowid=rowid
);
"""

_KV_DDL = """
CREATE TABLE IF NOT EXISTS knowledge (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    id          TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    tags        TEXT NOT NULL DEFAULT '',
    chunk_id    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge(source_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_path   ON knowledge(source_path);
CREATE INDEX IF NOT EXISTS idx_knowledge_id     ON knowledge(id);
"""


def ensure_tables(engine: StorageEngine) -> None:
    """Create the knowledge tables + FTS index if they don't exist."""
    # Use raw connection to run DDL
    with engine._lock:
        engine._conn.executescript(_KV_DDL)
        engine._conn.executescript(_FTS_DDL)
        engine._conn.commit()


# ---------------------------------------------------------------------------
# Ingest helpers
# ---------------------------------------------------------------------------

def _insert_doc(engine: StorageEngine, doc: KnowledgeDocument) -> None:
    """Insert one KnowledgeDocument into the knowledge table + FTS."""
    tags_str = ",".join(doc.tags)
    now_iso = (
        doc.created_at.isoformat()
        if isinstance(doc.created_at, str)
        else doc.created_at.isoformat()
    )

    with engine._lock:
        conn = engine._conn
        conn.execute(
            """INSERT INTO knowledge
               (id, source_type, source_path, title, content, tags, chunk_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc.id, doc.source_type, doc.source_path, doc.title, doc.content, tags_str, doc.chunk_id, now_iso),
        )
        conn.execute(
            """INSERT INTO knowledge_fts (rowid, title, content, tags)
               SELECT rowid, title, content, tags FROM knowledge WHERE id = ?""",
            (doc.id,),
        )
        conn.commit()


def ingest_single_file(
    engine: StorageEngine,
    file_path: Path,
    source_type: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingest one file. Returns number of chunks inserted."""
    ensure_tables(engine)
    docs = parse_markdown_file(file_path, source_type, chunk_size, chunk_overlap)
    for doc in docs:
        _insert_doc(engine, doc)
    return len(docs)


def ingest_directory(
    engine: StorageEngine,
    directory: str | Path,
    source_type: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingest all markdown/txt files in *directory* (recursive). Returns chunk count."""
    ensure_tables(engine)
    d = Path(directory)
    count = 0
    for ext in ("*.md", "*.txt"):
        for f in d.rglob(ext):
            if f.name.startswith("."):
                continue
            count += ingest_single_file(engine, f, source_type, chunk_size, chunk_overlap)
    return count


def ingest_domain_pack(
    engine: StorageEngine,
    pack_path: str | Path,
    pack_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingest the ``knowledge/`` directory inside a Domain Pack."""
    pack = Path(pack_path)
    knowledge_dir = pack / "knowledge"
    if not knowledge_dir.exists():
        return 0
    return ingest_directory(engine, knowledge_dir, f"domain:{pack_id}", chunk_size, chunk_overlap)
