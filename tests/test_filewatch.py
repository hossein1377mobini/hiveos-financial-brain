"""Tests for File Watch Folder service."""

import asyncio
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone

import pytest

from hiveos.storage import StorageEngine
from hiveos.knowledge.service import KnowledgeService
from hiveos.filewatch.models import (
    WatchFolder,
    WatchFolderStatus,
    FileEvent,
    FileEventKind,
    generate_folder_id,
)
from hiveos.filewatch.service import FileWatchService


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "filewatch_test.db"


@pytest.fixture
def engine(db_path):
    eng = StorageEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def knowledge_svc(engine):
    return KnowledgeService(engine)


@pytest.fixture
def filewatch_svc(engine, knowledge_svc):
    return FileWatchService(engine, knowledge_svc)


@pytest.fixture
def customer_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create sample files
        (root / "readme.md").write_text(
            "# Customer README\n\nThis is a customer document.\n",
            encoding="utf-8",
        )
        (root / "data.txt").write_text(
            "Customer data line 1\nCustomer data line 2\n",
            encoding="utf-8",
        )
        (root / "notes.md").write_text(
            "# Meeting Notes\n\nDiscussed project timeline.\n",
            encoding="utf-8",
        )
        # Hidden file (should be ignored)
        (root / ".hidden.txt").write_text("hidden\n", encoding="utf-8")
        yield root


# ── Model tests ────────────────────────────────────────────────────────


class TestWatchFolderModel:
    def test_create_folder(self):
        f = WatchFolder(folder_id="wf-test", name="Test", path="/tmp/test")
        assert f.folder_id == "wf-test"
        assert f.status == WatchFolderStatus.ACTIVE
        assert f.accepts_file(Path("doc.md"))
        assert f.accepts_file(Path("doc.txt"))
        assert not f.accepts_file(Path("doc.exe"))

    def test_custom_extensions(self):
        f = WatchFolder(
            folder_id="wf-x",
            name="X",
            path="/tmp/x",
            supported_extensions=[".md", ".csv"],
        )
        assert f.accepts_file(Path("data.csv"))
        assert not f.accepts_file(Path("data.txt"))

    def test_to_dict_roundtrip(self):
        f = WatchFolder(
            folder_id="wf-rt",
            name="Roundtrip",
            path="/tmp/rt",
            customer_id="cust-1",
            tags=["finance"],
        )
        d = f.to_dict()
        f2 = WatchFolder.from_dict(d)
        assert f2.folder_id == "wf-rt"
        assert f2.customer_id == "cust-1"
        assert f2.tags == ["finance"]
        assert f2.status == WatchFolderStatus.ACTIVE

    def test_generate_folder_id(self):
        id1 = generate_folder_id("My Customer")
        assert id1.startswith("wf-")
        assert "my-customer" in id1

        id2 = generate_folder_id("Another")
        assert id1 != id2


class TestFileEventModel:
    def test_create_event(self):
        e = FileEvent(folder_id="wf-1", file_path="/tmp/doc.md")
        assert e.event_id  # auto-generated
        assert e.event_kind == FileEventKind.CREATED
        assert e.timestamp  # auto-set

    def test_to_dict(self):
        e = FileEvent(
            folder_id="wf-1",
            file_path="/tmp/doc.md",
            event_kind=FileEventKind.INGESTED,
            chunks_ingested=3,
        )
        d = e.to_dict()
        assert d["event_kind"] == "ingested"
        assert d["chunks_ingested"] == 3


# ── Service CRUD tests ─────────────────────────────────────────────────


class TestFileWatchServiceCRUD:
    def test_add_folder(self, filewatch_svc, customer_dir):
        folder = filewatch_svc.add_folder(
            name="Test Customer",
            path=str(customer_dir),
            customer_id="cust-001",
        )
        assert folder.folder_id.startswith("wf-")
        assert folder.path == str(customer_dir.resolve())
        assert folder.customer_id == "cust-001"

    def test_get_folder(self, filewatch_svc, customer_dir):
        folder = filewatch_svc.add_folder(name="Get Me", path=str(customer_dir))
        got = filewatch_svc.get_folder(folder.folder_id)
        assert got is not None
        assert got.name == "Get Me"

    def test_list_folders(self, filewatch_svc, customer_dir):
        filewatch_svc.add_folder(name="A", path=str(customer_dir))
        filewatch_svc.add_folder(name="B", path=str(customer_dir))
        all_folders = filewatch_svc.list_folders()
        assert len(all_folders) == 2

    def test_list_by_customer(self, filewatch_svc, customer_dir):
        filewatch_svc.add_folder(name="X", path=str(customer_dir), customer_id="c1")
        filewatch_svc.add_folder(name="Y", path=str(customer_dir), customer_id="c2")
        c1 = filewatch_svc.list_folders(customer_id="c1")
        assert len(c1) == 1
        assert c1[0].customer_id == "c1"

    def test_update_folder(self, filewatch_svc, customer_dir):
        folder = filewatch_svc.add_folder(name="Old", path=str(customer_dir))
        updated = filewatch_svc.update_folder(
            folder.folder_id, name="New", tags=["updated"]
        )
        assert updated.name == "New"
        assert updated.tags == ["updated"]

    def test_pause_resume(self, filewatch_svc, customer_dir):
        folder = filewatch_svc.add_folder(name="Pause", path=str(customer_dir))
        assert folder.status == WatchFolderStatus.ACTIVE

        paused = filewatch_svc.update_folder(
            folder.folder_id, status=WatchFolderStatus.PAUSED
        )
        assert paused.status == WatchFolderStatus.PAUSED

        resumed = filewatch_svc.update_folder(
            folder.folder_id, status=WatchFolderStatus.ACTIVE
        )
        assert resumed.status == WatchFolderStatus.ACTIVE

    def test_remove_folder(self, filewatch_svc, customer_dir):
        folder = filewatch_svc.add_folder(name="Remove", path=str(customer_dir))
        assert filewatch_svc.remove_folder(folder.folder_id) is True
        assert filewatch_svc.get_folder(folder.folder_id) is None

    def test_remove_nonexistent(self, filewatch_svc):
        assert filewatch_svc.remove_folder("wf-nope") is False


# ── Ingestion tests ────────────────────────────────────────────────────


class TestFileWatchIngestion:
    def test_scan_folder(self, filewatch_svc, customer_dir):
        """Scan should ingest all eligible files."""
        folder = filewatch_svc.add_folder(
            name="Scan", path=str(customer_dir)
        )
        count = filewatch_svc.scan_folder(folder.folder_id)
        assert count > 0

        # Check the folder's counter updated
        updated = filewatch_svc.get_folder(folder.folder_id)
        assert updated.total_files_ingested > 0

    def test_events_logged(self, filewatch_svc, customer_dir):
        """Scan should create file events."""
        folder = filewatch_svc.add_folder(
            name="Events", path=str(customer_dir)
        )
        filewatch_svc.scan_folder(folder.folder_id)

        events = filewatch_svc.get_events(folder_id=folder.folder_id)
        assert len(events) > 0
        assert all(e.event_kind == FileEventKind.INGESTED for e in events)

    def test_hidden_files_ignored(self, filewatch_svc, customer_dir):
        """Hidden files (starting with .) should be skipped."""
        folder = filewatch_svc.add_folder(
            name="Hidden", path=str(customer_dir)
        )
        filewatch_svc.scan_folder(folder.folder_id)
        events = filewatch_svc.get_events(folder_id=folder.folder_id)
        paths = [e.file_path for e in events]
        assert not any(".hidden" in p for p in paths)

    def test_new_file_detected(self, filewatch_svc, customer_dir):
        """Watcher should detect a new file dropped into the folder."""
        folder = filewatch_svc.add_folder(
            name="WatchNew", path=str(customer_dir)
        )
        # Let the watcher take a snapshot
        time.sleep(0.3)

        # Drop a new file
        (customer_dir / "new_file.md").write_text(
            "# New Document\n\nFresh content.\n", encoding="utf-8"
        )

        # Wait for poll cycle
        time.sleep(6)

        events = filewatch_svc.get_events(folder_id=folder.folder_id)
        new_events = [e for e in events if "new_file" in e.file_path]
        assert len(new_events) > 0

    def test_create_folder_auto_ingests(self, filewatch_svc, customer_dir):
        """Adding a folder should trigger initial scan."""
        folder = filewatch_svc.add_folder(
            name="AutoIngest", path=str(customer_dir)
        )
        # Wait for initial scan
        time.sleep(1)
        updated = filewatch_svc.get_folder(folder.folder_id)
        assert updated.total_files_ingested > 0


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_nonexistent_folder_path(self, filewatch_svc):
        """Adding a folder with a non-existent path should create it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = str(Path(tmpdir) / "new_dir")
            folder = filewatch_svc.add_folder(name="New", path=new_path)
            assert Path(new_path).exists()

    def test_empty_folder_scan(self, filewatch_svc):
        """Scanning an empty folder returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = filewatch_svc.add_folder(name="Empty", path=tmpdir)
            count = filewatch_svc.scan_folder(folder.folder_id)
            assert count == 0

    def test_get_events_empty(self, filewatch_svc):
        """No events returns empty list."""
        events = filewatch_svc.get_events()
        assert events == []

    def test_stop_all(self, filewatch_svc, customer_dir):
        """stop_all should cleanly stop all watchers."""
        filewatch_svc.add_folder(name="A", path=str(customer_dir))
        filewatch_svc.add_folder(name="B", path=str(customer_dir))
        filewatch_svc.stop_all()
        assert len(filewatch_svc._watchers) == 0
