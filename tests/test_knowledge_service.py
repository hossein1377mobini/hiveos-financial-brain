"""Tests for the Knowledge Service."""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from hiveos.storage import StorageEngine
from hiveos.knowledge.models import KnowledgeDocument, KnowledgeResult, SourceInfo, IndexStats
from hiveos.knowledge.indexing import (
    extract_frontmatter,
    auto_tags_from_content,
    parse_markdown_file,
    _chunk_text,
)
from hiveos.knowledge.search import _escape_fts5, search_fts5
from hiveos.knowledge.ingestion import ensure_tables, ingest_single_file, ingest_directory, ingest_domain_pack
from hiveos.knowledge.service import KnowledgeService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "knowledge_test.db"


@pytest.fixture
def engine(db_path):
    eng = StorageEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def svc(engine):
    return KnowledgeService(engine)


@pytest.fixture
def knowledge_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create sample markdown files
        (root / "intro.md").write_text(
            "---\ntitle: Introduction\n---\n\n# Introduction\n\nWelcome to HiveOS.\n"
            "HiveOS is an organisational intelligence platform.\n",
            encoding="utf-8",
        )
        (root / "tax.md").write_text(
            "# Tax Rules\n\nAll invoices must be filed within 30 days.\n",
            encoding="utf-8",
        )
        (root / "payroll.md").write_text(
            "# Payroll Process\n\nStep 1: Collect timesheets\nStep 2: Run payroll\nStep 3: Distribute payslips\n",
            encoding="utf-8",
        )
        yield root


# ---------------------------------------------------------------------------
# Unit tests — indexing
# ---------------------------------------------------------------------------

class TestExtractFrontmatter:
    def test_extracts_frontmatter(self):
        content = "---\ntitle: Hello\ntags: [a, b]\n---\nBody here"
        fm, body = extract_frontmatter(content)
        assert fm["title"] == "Hello"
        assert fm["tags"] == ["a", "b"]
        assert body.strip() == "Body here"

    def test_no_frontmatter(self):
        fm, body = extract_frontmatter("# Just a header\nBody")
        assert fm == {}
        assert body.startswith("# Just a header")

    def test_empty_frontmatter(self):
        fm, body = extract_frontmatter("---\n\n---\nBody")
        assert fm == {}


class TestAutoTags:
    def test_from_headings(self):
        text = "# Big Topic\n## Sub Topic\n### Detail\nSome body"
        tags = auto_tags_from_content(text)
        assert tags == ["big-topic", "sub-topic", "detail"]

    def test_no_headings(self):
        assert auto_tags_from_content("Just plain text with no headings") == []

    def test_special_characters_cleaned(self):
        tags = auto_tags_from_content("## What is FTS5?")
        assert tags == ["what-is-fts5"]


class TestChunkText:
    def test_small_text_single_chunk(self):
        chunks = _chunk_text("Short", 1000, 200)
        assert len(chunks) == 1
        assert chunks[0] == "Short"

    def test_empty_text(self):
        chunks = _chunk_text("", 1000, 200)
        assert chunks == [""]

    def test_large_text_multiple_chunks(self):
        text = "A" * 2500
        chunks = _chunk_text(text, 1000, 200)
        assert len(chunks) >= 3
        # Overlap means chunks are smaller than text length
        for chunk in chunks:
            assert len(chunk) <= 1000


class TestParseMarkdown:
    def test_with_frontmatter(self, knowledge_dir):
        docs = parse_markdown_file(knowledge_dir / "intro.md", "org")
        assert len(docs) >= 1
        doc = docs[0]
        assert doc.source_type == "org"
        assert doc.title == "Introduction"
        assert "introduction" in doc.tags

    def test_auto_tags(self, knowledge_dir):
        docs = parse_markdown_file(knowledge_dir / "tax.md", "org")
        assert docs[0].tags == ["tax-rules"]

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        docs = parse_markdown_file(f, "org")
        assert len(docs) == 1  # Should still produce one chunk

    def test_no_overlap_duplicate(self, knowledge_dir):
        docs = parse_markdown_file(knowledge_dir / "payroll.md", "org", chunk_size=1000, chunk_overlap=200)
        assert len(docs) >= 1


# ---------------------------------------------------------------------------
# Unit tests — FTS5 escaping
# ---------------------------------------------------------------------------

class TestFTS5Escape:
    def test_simple_query(self):
        assert _escape_fts5("hello world") == '"hello" "world"'

    def test_special_chars_stripped(self):
        result = _escape_fts5('what("is") this-*')
        assert '"' in result
        assert "(" not in result
        assert ")" not in result

    def test_empty_query(self):
        assert _escape_fts5("") == '""'


# ---------------------------------------------------------------------------
# Integration tests — full service
# ---------------------------------------------------------------------------

class TestKnowledgeService:
    def test_ingest_single_document(self, svc):
        doc = KnowledgeDocument(
            id="doc-1",
            source_type="org",
            source_path="/docs/test.md",
            title="Test Document",
            content="This is test content about invoicing.",
            tags=["invoicing", "test"],
            chunk_id=0,
        )
        doc_id = asyncio.run(svc.ingest_document(doc))
        assert doc_id == "doc-1"
        # Verify retrievable
        fetched = asyncio.run(svc.get_document("doc-1"))
        assert fetched is not None
        assert fetched.title == "Test Document"

    def test_ingest_directory(self, svc, knowledge_dir):
        count = asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        assert count >= 3  # 3 files
        stats = asyncio.run(svc.stats())
        assert stats.total_chunks >= 3

    def test_search_basic(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        results = asyncio.run(svc.search("invoices"))
        assert len(results) >= 1
        assert "invoices" in results[0].snippet.lower()

    def test_search_no_results(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        results = asyncio.run(svc.search("quantum physics"))
        assert results == []

    def test_search_with_source_filter(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "domain:accounting"))
        results = asyncio.run(svc.search("invoices", source_filter="domain:accounting"))
        assert len(results) >= 1

    def test_search_source_filter_excludes(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        results = asyncio.run(svc.search("invoices", source_filter="domain:accounting"))
        assert len(results) == 0

    def test_search_with_tag_filter(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        results = asyncio.run(svc.search("HiveOS", tags=["introduction"]))
        assert len(results) >= 1

    def test_combined_filters(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "domain:hr"))
        # Source filter + tag filter
        results = asyncio.run(svc.search("HiveOS", source_filter="org", tags=["introduction"]))
        assert len(results) >= 1
        assert all(r.source_type == "org" for r in results)

    def test_delete_document(self, svc):
        doc = KnowledgeDocument(
            id="to-delete",
            source_type="org",
            source_path="/x.md",
            title="Delete me",
            content="Body text here",
            tags=[],
        )
        asyncio.run(svc.ingest_document(doc))
        deleted = asyncio.run(svc.delete_document("to-delete"))
        assert deleted is True
        fetched = asyncio.run(svc.get_document("to-delete"))
        assert fetched is None

    def test_delete_nonexistent(self, svc):
        deleted = asyncio.run(svc.delete_document("no-such-id"))
        assert deleted is False

    def test_list_sources(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "domain:accounting"))
        sources = asyncio.run(svc.list_sources())
        source_types = [s.source_type for s in sources]
        assert "org" in source_types
        assert "domain:accounting" in source_types

    def test_stats(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        stats = asyncio.run(svc.stats())
        assert stats.total_chunks >= 3
        assert stats.total_documents >= 3
        assert stats.total_sources >= 1

    def test_stats_empty(self, svc):
        stats = asyncio.run(svc.stats())
        assert stats.total_chunks == 0
        assert stats.total_documents == 0

    def test_ingest_domain_pack(self, svc):
        with tempfile.TemporaryDirectory() as tmpdir:
            pack = Path(tmpdir) / "my-pack"
            knowledge = pack / "knowledge"
            knowledge.mkdir(parents=True)
            (knowledge / "pack_doc.md").write_text(
                "# Pack Knowledge\nDomain-specific content here.\n",
                encoding="utf-8",
            )
            count = asyncio.run(svc.ingest_domain_pack(str(pack), "accounting"))
            assert count >= 1
            # Verify source type is domain:accounting
            results = asyncio.run(svc.search("domain-specific"))
            assert any(r.source_type == "domain:accounting" for r in results)

    def test_ingest_empty_domain_pack(self, svc):
        with tempfile.TemporaryDirectory() as tmpdir:
            pack = Path(tmpdir) / "empty-pack"
            pack.mkdir()
            count = asyncio.run(svc.ingest_domain_pack(str(pack), "empty"))
            assert count == 0

    def test_search_limit(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        results = asyncio.run(svc.search("a", limit=2))
        assert len(results) <= 2

    def test_special_characters_in_query(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        # Should not raise
        results = asyncio.run(svc.search("what IS this??!"))
        assert isinstance(results, list)

    def test_search_empty_index(self, svc):
        results = asyncio.run(svc.search("anything"))
        assert results == []

    def test_frontmatter_title_used(self, svc, knowledge_dir):
        asyncio.run(svc.ingest_directory(str(knowledge_dir), "org"))
        doc = asyncio.run(svc.get_document("intro.md"))
        # Title from frontmatter or fallback to stem
        results = asyncio.run(svc.search("Introduction"))
        assert len(results) >= 1
