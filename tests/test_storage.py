"""Tests for HiveOS Storage Engine."""

import json
import os
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

from hiveos.storage import StorageEngine


class TestStorageEngine:
    """SQLite persistence layer tests."""

    @pytest.fixture
    def db_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test.db"

    @pytest.fixture
    def storage(self, db_path):
        s = StorageEngine(db_path)
        yield s
        s.close()
        if db_path.exists():
            db_path.unlink()

    def test_init_creates_db(self, db_path):
        assert not db_path.exists()
        s = StorageEngine(db_path)
        assert db_path.exists()
        s.close()

    def test_upsert_and_load(self, storage):
        storage.upsert("test", "k1", {"name": "alice", "value": 42})
        loaded = storage.load("test", "k1")
        assert loaded is not None
        assert loaded["name"] == "alice"
        assert loaded["value"] == 42

    def test_load_missing(self, storage):
        assert storage.load("nonexistent", "nope") is None

    def test_upsert_overwrite(self, storage):
        storage.upsert("test", "k1", {"version": 1})
        storage.upsert("test", "k1", {"version": 2})
        loaded = storage.load("test", "k1")
        assert loaded["version"] == 2

    def test_load_all(self, storage):
        storage.upsert("ns1", "a", {"val": 1})
        storage.upsert("ns1", "b", {"val": 2})
        storage.upsert("ns2", "c", {"val": 3})
        results = storage.load_all("ns1")
        assert len(results) == 2
        vals = [r["val"] for r in results]
        assert 1 in vals
        assert 2 in vals

    def test_load_all_with_keys(self, storage):
        storage.upsert("ns", "x", {"data": "first"})
        storage.upsert("ns", "y", {"data": "second"})
        result = storage.load_all_with_keys("ns")
        assert set(result.keys()) == {"x", "y"}
        assert result["x"]["data"] == "first"
        assert result["y"]["data"] == "second"

    def test_delete(self, storage):
        storage.upsert("ns", "k1", {"val": 1})
        storage.upsert("ns", "k2", {"val": 2})
        storage.delete("ns", "k1")
        assert storage.load("ns", "k1") is None
        assert storage.load("ns", "k2") is not None

    def test_clear_namespace(self, storage):
        storage.upsert("ns1", "a", {})
        storage.upsert("ns1", "b", {})
        storage.upsert("ns2", "c", {})
        storage.clear("ns1")
        assert storage.count("ns1") == 0
        assert storage.count("ns2") == 1

    def test_count(self, storage):
        assert storage.count("empty") == 0
        storage.upsert("ns", "a", {})
        storage.upsert("ns", "b", {})
        assert storage.count("ns") == 2

    def test_persistence_across_instances(self, db_path):
        s1 = StorageEngine(db_path)
        s1.upsert("ns", "persist", {"data": "hello"})
        s1.close()

        s2 = StorageEngine(db_path)
        loaded = s2.load("ns", "persist")
        assert loaded is not None
        assert loaded["data"] == "hello"
        s2.close()

    def test_default_path(self):
        """Default path should be ~/.hiveos/data/hiveos.db"""
        s = StorageEngine()
        expected = Path.home() / ".hiveos" / "data" / "hiveos.db"
        assert str(s._db_path) == str(expected)
        s.close()

    def test_complex_nested_data(self, storage):
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": {"key": "value"}},
            "dates": ["2024-01-01T00:00:00+00:00"],
        }
        storage.upsert("ns", "complex", data)
        loaded = storage.load("ns", "complex")
        assert loaded["string"] == "hello"
        assert loaded["number"] == 42
        assert loaded["bool"] is True
        assert loaded["null"] is None
        assert loaded["list"] == [1, 2, 3]
        assert loaded["dict"]["nested"]["key"] == "value"

    def test_vacuum(self, storage):
        storage.upsert("ns", "x", {"v": 1})
        storage.delete("ns", "x")
        storage.vacuum()  # Should not raise
        assert storage.count("ns") == 0
