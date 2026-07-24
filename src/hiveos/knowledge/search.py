"""Search engine — FTS5 queries with BM25 scoring and filtering."""

from __future__ import annotations

import re
from typing import List, Optional

from hiveos.knowledge.models import KnowledgeResult


def _escape_fts5(text: str) -> str:
    """Escape special FTS5 characters and wrap each token in quotes."""
    # Strip any stray FTS5 operators / quotes
    cleaned = re.sub(r'["*^()\-\[\]:]', " ", text)
    tokens = cleaned.split()
    if not tokens:
        return '""'
    # Wrap each token for safety, join with implicit AND
    parts = [f'"{t}"' for t in tokens]
    return " ".join(parts)


def search_fts5(
    fetch_all_fn,
    query: str,
    source_filter: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
) -> List[KnowledgeResult]:
    """Run an FTS5 search against the knowledge_fts virtual table.

    Parameters
    ----------
    fetch_all_fn : callable
        ``StorageEngine.fetch_all(sql, params)``
    query : str
        User search string.
    source_filter : str | None
        Filter by source_type (e.g. ``"domain:accounting"`` or ``"org"``).
    tags : list[str] | None
        AND filter — every listed tag must be present on the chunk.
    limit : int
        Maximum results.

    Returns
    -------
    list[KnowledgeResult]
        Sorted by BM25 score descending.
    """
    fts_query = _escape_fts5(query)

    # Build SQL
    where_clauses: list[str] = ["knowledge_fts MATCH ?"]
    params: list[object] = [fts_query]

    if source_filter:
        where_clauses.append("k.source_type = ?")
        params.append(source_filter)

    # Tag filters — each tag must be in the comma-separated tags column
    if tags:
        for tag in tags:
            where_clauses.append("(',' || k.tags || ',') LIKE ?")
            params.append(f"%,{tag},%")

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            k.id,
            k.source_type,
            k.source_path,
            k.title,
            snippet(knowledge_fts, 1, '<b>', '</b>', '...', 64) AS snippet,
            bm25(knowledge_fts) AS score,
            k.chunk_id,
            k.tags
        FROM knowledge_fts
        JOIN knowledge k ON knowledge_fts.rowid = k.rowid
        WHERE {where_sql}
        ORDER BY bm25(knowledge_fts)
        LIMIT ?
    """
    params.append(limit)

    rows = fetch_all_fn(sql, tuple(params))
    results: List[KnowledgeResult] = []
    for row in rows:
        doc_id, src_type, src_path, title, snippet, score, chunk_id, tags_raw = row
        tag_list = [t.strip() for t in (tags_raw or "").split(",") if t.strip()]
        results.append(
            KnowledgeResult(
                doc_id=doc_id,
                source_type=src_type,
                source_path=src_path,
                title=title,
                snippet=snippet or "",
                score=score,
                chunk_id=chunk_id,
                tags=tag_list,
            )
        )
    return results
