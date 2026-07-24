"""Tests for Domain Pack Downloader and Registry Client.

Uses mocked HTTP to test without network access.
"""

import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hiveos.domain_pack.downloader import (
    DomainPackDownloader,
    DownloadError,
    DownloadProgress,
    InstallResult,
)
from hiveos.domain_pack.registry_client import (
    PackListing,
    RegistryClient,
    RegistryClientError,
    SearchResults,
)
from hiveos.domain_pack.manager import DomainPackManager, DomainPackError


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_pack_dir(tmp_path):
    """Create a valid minimal Domain Pack directory."""
    pack_dir = tmp_path / "test-domain"
    pack_dir.mkdir()
    (pack_dir / "knowledge").mkdir()
    (pack_dir / "skills").mkdir()

    # domain.yaml
    (pack_dir / "domain.yaml").write_text(
        "id: test-domain\n"
        "version: 1.0.0\n"
        "name: Test Domain Pack\n"
        "description: A test pack\n"
        "min_core_version: 1.0.0\n"
        "author:\n"
        "  name: Test\n"
        "  url: https://test.com\n"
        "skills:\n"
        "  - id: test-skill\n",
        encoding="utf-8",
    )

    # knowledge file
    (pack_dir / "knowledge" / "test-knowledge.md").write_text(
        "# Test Knowledge\nSome content.", encoding="utf-8"
    )

    # skill file
    (pack_dir / "skills" / "test-skill.yaml").write_text(
        "id: test-skill\n"
        "name: Test Skill\n"
        "version: 1.0.0\n"
        "description: A test skill\n"
        "input_schema:\n"
        "  type: object\n"
        "output_schema:\n"
        "  type: object\n"
        "instruction: Do something\n",
        encoding="utf-8",
    )

    return pack_dir


@pytest.fixture
def pack_archive(tmp_path, sample_pack_dir):
    """Create a .tar.gz archive of the sample pack."""
    archive_path = tmp_path / "test-domain-1.0.0.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(sample_pack_dir, arcname="test-domain")
    return archive_path


@pytest.fixture
def mock_registry_response():
    """Sample registry API response for pack listing."""
    return {
        "packs": [
            {
                "id": "accounting",
                "name": "Accounting Domain Pack",
                "version": "1.2.0",
                "description": "Iranian accounting pack",
                "author": "HiveOS",
                "tags": ["accounting", "finance"],
                "downloads": 150,
                "size_bytes": 24576,
                "download_url": "https://registry.hiveos.dev/api/v1/packs/accounting/download",
                "sha256": hashlib.sha256(b"fake-content").hexdigest(),
                "min_core_version": "1.0.0",
                "published_at": "2026-01-15T10:00:00Z",
                "updated_at": "2026-07-01T12:00:00Z",
            },
            {
                "id": "legal",
                "name": "Legal Domain Pack",
                "version": "2.0.0",
                "description": "Legal document processing",
                "author": "HiveOS",
                "tags": ["legal"],
                "downloads": 89,
                "size_bytes": 18432,
                "download_url": "https://registry.hiveos.dev/api/v1/packs/legal/download",
                "sha256": "",
                "min_core_version": "1.0.0",
                "published_at": "2026-02-20T08:00:00Z",
                "updated_at": "2026-06-15T14:00:00Z",
            },
        ],
        "total": 2,
        "page": 1,
        "per_page": 20,
    }


@pytest.fixture
def mock_search_response():
    """Sample search API response."""
    return {
        "query": "accounting",
        "packs": [
            {
                "id": "accounting",
                "name": "Accounting Domain Pack",
                "version": "1.2.0",
                "description": "Iranian accounting pack",
                "author": "HiveOS",
                "tags": ["accounting"],
                "downloads": 150,
                "size_bytes": 24576,
                "download_url": "",
                "sha256": "",
                "min_core_version": "1.0.0",
                "published_at": "",
                "updated_at": "",
            },
        ],
        "total": 1,
    }


# ── RegistryClient Tests ──────────────────────────────────────────────


class TestRegistryClientParsing:
    """Test response parsing logic (no network)."""

    def test_parse_pack_listing(self):
        data = {
            "id": "test",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "desc",
            "author": "author",
            "tags": ["tag1"],
            "downloads": 10,
            "size_bytes": 1024,
            "download_url": "http://example.com/dl",
            "sha256": "abc123",
            "min_core_version": "1.0.0",
            "published_at": "2026-01-01",
            "updated_at": "2026-06-01",
        }
        client = RegistryClient.__new__(RegistryClient)
        listing = client._parse_pack_listing(data)

        assert listing.id == "test"
        assert listing.name == "Test Pack"
        assert listing.version == "1.0.0"
        assert listing.tags == ["tag1"]
        assert listing.downloads == 10
        assert listing.size_bytes == 1024
        assert listing.sha256 == "abc123"

    def test_parse_search_results_list(self):
        data = [
            {"id": "a", "name": "A", "version": "1.0.0"},
            {"id": "b", "name": "B", "version": "2.0.0"},
        ]
        client = RegistryClient.__new__(RegistryClient)
        results = client._parse_search_results(data)

        assert results.total == 2
        assert len(results.packs) == 2
        assert results.packs[0].id == "a"

    def test_parse_search_results_dict(self):
        data = {
            "query": "test",
            "total": 1,
            "packs": [{"id": "x", "name": "X", "version": "1.0.0"}],
        }
        client = RegistryClient.__new__(RegistryClient)
        results = client._parse_search_results(data)

        assert results.query == "test"
        assert results.total == 1
        assert results.packs[0].id == "x"

    def test_parse_empty_response(self):
        client = RegistryClient.__new__(RegistryClient)
        results = client._parse_search_results({"packs": []})
        assert results.total == 0
        assert len(results.packs) == 0

    def test_build_url_no_params(self):
        client = RegistryClient(base_url="https://example.com/api")
        url = client._build_url("/packs")
        assert url == "https://example.com/api/packs"

    def test_build_url_with_params(self):
        client = RegistryClient(base_url="https://example.com/api")
        url = client._build_url("/packs", {"q": "test", "page": "1"})
        assert "q=test" in url
        assert "page=1" in url
        assert url.startswith("https://example.com/api/packs?")

    def test_build_download_url_with_version(self):
        client = RegistryClient(base_url="https://example.com/api")
        url = client._build_download_url("accounting", "1.2.0")
        assert url == "https://example.com/api/packs/accounting/versions/1.2.0/download"

    def test_build_download_url_latest(self):
        client = RegistryClient(base_url="https://example.com/api")
        url = client._build_download_url("accounting", None)
        assert url == "https://example.com/api/packs/accounting/download"


class TestRegistryClientCache:
    """Test cache read/write logic."""

    def test_cache_key_deterministic(self, tmp_path):
        client = RegistryClient(cache_dir=tmp_path)
        key1 = client._cache_key("https://example.com/api/packs")
        key2 = client._cache_key("https://example.com/api/packs")
        assert key1 == key2

    def test_cache_key_different_urls(self, tmp_path):
        client = RegistryClient(cache_dir=tmp_path)
        key1 = client._cache_key("https://example.com/api/packs")
        key2 = client._cache_key("https://example.com/api/packs/search")
        assert key1 != key2

    def test_write_read_cache(self, tmp_path):
        client = RegistryClient(cache_dir=tmp_path)
        key = client._cache_key("https://example.com/test")
        data = {"result": "ok"}

        client._write_cache(key, data)
        cached = client._read_cache(key)
        assert cached == data

    def test_cache_expired(self, tmp_path):
        client = RegistryClient(cache_dir=tmp_path, cache_ttl=0)
        key = client._cache_key("https://example.com/test")
        client._write_cache(key, {"data": 1})

        # TTL=0 means cache is always expired
        cached = client._read_cache(key)
        assert cached is None

    def test_cache_nonexistent(self, tmp_path):
        client = RegistryClient(cache_dir=tmp_path)
        key = client._cache_key("https://example.com/nonexistent")
        cached = client._read_cache(key)
        assert cached is None


class TestPackListing:
    """Test PackListing data model."""

    def test_to_dict(self):
        listing = PackListing(
            id="test",
            name="Test",
            version="1.0.0",
            tags=["a", "b"],
        )
        d = listing.to_dict()
        assert d["id"] == "test"
        assert d["tags"] == ["a", "b"]
        assert d["downloads"] == 0

    def test_defaults(self):
        listing = PackListing(id="x", name="X", version="1.0.0")
        assert listing.description == ""
        assert listing.author == ""
        assert listing.tags == []
        assert listing.downloads == 0
        assert listing.sha256 == ""


# ── DomainPackDownloader Tests ────────────────────────────────────────


class TestDomainPackDownloader:
    """Test downloader orchestration with mocked registry."""

    def _make_downloader(self, tmp_path, mock_client=None):
        """Create a downloader with mocked client."""
        base_dir = tmp_path / "domains"
        base_dir.mkdir()
        # Use unique DB per test to avoid shared state
        db_path = tmp_path / "test.db"
        from hiveos.storage import StorageEngine
        storage = StorageEngine(db_path=db_path)
        mgr = DomainPackManager(base_dir=base_dir, storage=storage)

        downloader = DomainPackDownloader.__new__(DomainPackDownloader)
        downloader._manager = mgr
        downloader._cache_dir = tmp_path / "cache"
        downloader._cache_dir.mkdir()
        downloader._client = mock_client or RegistryClient(cache_dir=downloader._cache_dir)
        return downloader

    def test_extract_archive(self, tmp_path, pack_archive):
        downloader = self._make_downloader(tmp_path)
        extract_dir = downloader._extract_archive(pack_archive, "test-domain")

        assert extract_dir.exists()
        assert (extract_dir / "test-domain" / "domain.yaml").exists()

    def test_extract_archive_block_traversal(self, tmp_path):
        """Archive with path traversal should be rejected."""
        bad_archive = tmp_path / "bad.tar.gz"
        with tarfile.open(bad_archive, "w:gz") as tar:
            info = tarfile.TarInfo(name="../escape/evil.txt")
            info.size = 4
            tar.addfile(info, io.BytesIO(b"evil"))

        downloader = self._make_downloader(tmp_path)
        with pytest.raises(DownloadError, match="path traversal"):
            downloader._extract_archive(bad_archive, "test")

    def test_extract_archive_block_absolute(self, tmp_path):
        """Archive with absolute paths should be rejected."""
        bad_archive = tmp_path / "bad2.tar.gz"
        with tarfile.open(bad_archive, "w:gz") as tar:
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = 4
            tar.addfile(info, io.BytesIO(b"root"))

        downloader = self._make_downloader(tmp_path)
        with pytest.raises(DownloadError, match="absolute path"):
            downloader._extract_archive(bad_archive, "test")

    def test_find_pack_root_at_root(self, tmp_path):
        downloader = self._make_downloader(tmp_path)
        d = tmp_path / "extracted" / "pack"
        d.mkdir(parents=True)
        (d / "domain.yaml").write_text("id: test")

        root = downloader._find_pack_root(d)
        assert root == d

    def test_find_pack_root_in_subdir(self, tmp_path):
        downloader = self._make_downloader(tmp_path)
        d = tmp_path / "extracted" / "wrapper"
        sub = d / "test-domain"
        sub.mkdir(parents=True)
        (sub / "domain.yaml").write_text("id: test")

        root = downloader._find_pack_root(d)
        assert root == sub

    def test_find_pack_root_not_found(self, tmp_path):
        downloader = self._make_downloader(tmp_path)
        d = tmp_path / "empty"
        d.mkdir()

        root = downloader._find_pack_root(d)
        assert root is None

    def test_download_and_install(self, tmp_path, sample_pack_dir, pack_archive):
        """Full download-and-install pipeline with mocked HTTP."""
        downloader = self._make_downloader(tmp_path)

        # Mock the client to return our archive
        downloader._client.download_pack = MagicMock(return_value=pack_archive)
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(
                id="test-domain",
                name="Test Domain Pack",
                version="1.0.0",
            )
        )

        progress_log = []

        def capture_progress(p):
            progress_log.append(p)

        result = downloader.download_and_install(
            "test-domain",
            on_progress=capture_progress,
        )

        assert result.success is True
        assert result.pack_id == "test-domain"
        assert result.version == "1.0.0"
        assert result.metadata is not None
        assert result.metadata.name == "Test Domain Pack"
        assert "download" in result.phases
        assert "extract" in result.phases
        assert "validate" in result.phases
        assert "install" in result.phases

        # Verify progress was emitted
        phases_seen = [p.phase for p in progress_log]
        assert "done" in phases_seen

    def test_download_network_error(self, tmp_path):
        """Download failure returns error result."""
        downloader = self._make_downloader(tmp_path)
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(id="x", name="X", version="1.0.0")
        )
        downloader._client.download_pack = MagicMock(
            side_effect=RegistryClientError("Network timeout")
        )

        result = downloader.download_and_install("x")
        assert result.success is False
        assert "Network timeout" in result.error

    def test_download_invalid_archive(self, tmp_path):
        """Archive without domain.yaml returns error."""
        downloader = self._make_downloader(tmp_path)

        # Create empty archive
        empty_archive = tmp_path / "empty.tar.gz"
        with tarfile.open(empty_archive, "w:gz") as tar:
            pass  # empty

        downloader._client.download_pack = MagicMock(return_value=empty_archive)
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(id="x", name="X", version="1.0.0")
        )

        result = downloader.download_and_install("x")
        assert result.success is False
        assert "valid Domain Pack" in result.error

    def test_search(self, tmp_path, mock_search_response):
        downloader = self._make_downloader(tmp_path)
        downloader._client.search = MagicMock(
            return_value=SearchResults(
                query="accounting",
                total=1,
                packs=[PackListing(id="accounting", name="Accounting", version="1.2.0")],
            )
        )

        results = downloader.search("accounting")
        assert results.total == 1
        assert results.packs[0].id == "accounting"

    def test_get_available(self, tmp_path):
        downloader = self._make_downloader(tmp_path)
        downloader._client.list_packs = MagicMock(
            return_value=SearchResults(
                query="",
                total=2,
                packs=[
                    PackListing(id="a", name="A", version="1.0.0"),
                    PackListing(id="b", name="B", version="2.0.0"),
                ],
            )
        )

        packs = downloader.get_available()
        assert len(packs) == 2

    def test_get_pack_info(self, tmp_path):
        downloader = self._make_downloader(tmp_path)
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(
                id="test", name="Test", version="1.0.0", description="desc"
            )
        )

        info = downloader.get_pack_info("test")
        assert info is not None
        assert info.id == "test"

    def test_get_installed_info(self, tmp_path, sample_pack_dir):
        downloader = self._make_downloader(tmp_path)

        # Install a pack first (use asyncio.run for async method)
        import asyncio
        asyncio.run(downloader._manager.install(sample_pack_dir))

        # Mock remote check
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(
                id="test-domain",
                name="Test Domain Pack",
                version="1.0.0",
            )
        )

        info = downloader.get_installed_info()
        assert len(info) == 1
        assert info[0]["id"] == "test-domain"
        assert info[0]["update_available"] is False

    def test_update_pack_already_up_to_date(self, tmp_path, sample_pack_dir):
        downloader = self._make_downloader(tmp_path)

        # Install pack
        import asyncio
        asyncio.run(downloader._manager.install(sample_pack_dir))

        # Registry has same version
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(
                id="test-domain",
                name="Test",
                version="1.0.0",
            )
        )

        result = downloader.update_pack("test-domain")
        assert result.success is True
        assert "check" in result.phases

    def test_progress_callback(self, tmp_path, pack_archive):
        downloader = self._make_downloader(tmp_path)
        downloader._client.download_pack = MagicMock(return_value=pack_archive)
        downloader._client.get_pack = MagicMock(
            return_value=PackListing(id="test-domain", name="Test", version="1.0.0")
        )

        phases = []
        downloader.download_and_install(
            "test-domain",
            on_progress=lambda p: phases.append(p.phase),
        )

        assert "download" in phases
        assert "extract" in phases
        assert "validate" in phases
        assert "install" in phases
        assert "done" in phases


# ── DownloadProgress & InstallResult Tests ─────────────────────────────


class TestDataClasses:
    def test_download_progress(self):
        p = DownloadProgress(pack_id="x", phase="download", message="Downloading...")
        assert p.pack_id == "x"
        assert p.phase == "download"
        assert p.percent == 0.0

    def test_install_result_success(self):
        r = InstallResult(success=True, pack_id="x", version="1.0.0", phases=["download", "install"])
        assert r.success is True
        assert r.error == ""
        assert len(r.phases) == 2

    def test_install_result_failure(self):
        r = InstallResult(success=False, pack_id="x", error="Network error")
        assert r.success is False
        assert r.error == "Network error"
