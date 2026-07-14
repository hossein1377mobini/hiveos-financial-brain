"""Tests for HiveOS Storage Migration system."""

import tempfile
import sqlite3
import pytest
from pathlib import Path

from hiveos.storage import StorageEngine, MigrationRunner, Migration
from hiveos.storage.migrations import get_builtin_migrations


class TestMigrationRunner:
    """Unit tests for MigrationRunner."""

    @pytest.fixture
    def conn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            c = sqlite3.connect(str(db))
            yield c
            c.close()
            if db.exists():
                db.unlink()

    @pytest.fixture
    def runner(self, conn):
        return MigrationRunner(conn)

    def test_init_creates_table(self, conn):
        runner = MigrationRunner(conn)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        assert tables is not None
        assert tables[0] == "schema_migrations"

    def test_applied_versions_empty(self, runner):
        assert runner.applied_versions() == []

    def test_register_and_run(self, runner):
        applied = []

        def m1(c):
            applied.append(1)
        runner.register(Migration(1, "first", m1))
        assert runner.run_all() == [1]
        assert applied == [1]
        assert runner.applied_versions() == [1]

    def test_no_reapply(self, runner):
        applied = []

        def m1(c):
            applied.append(1)
        runner.register(Migration(1, "first", m1))
        runner.run_all()
        assert applied == [1]
        # Second run should do nothing
        assert runner.run_all() == []
        assert applied == [1]

    def test_sequential_versions(self, runner):
        order = []

        def m1(c):
            order.append(1)
        def m2(c):
            order.append(2)
        def m3(c):
            order.append(3)

        runner.register_all([Migration(2, "second", m2), Migration(1, "first", m1), Migration(3, "third", m3)])
        assert runner.run_all() == [1, 2, 3]
        assert order == [1, 2, 3]

    def test_run_to(self, runner):
        order = []

        def m1(c): order.append(1)
        def m2(c): order.append(2)
        def m3(c): order.append(3)

        runner.register_all([
            Migration(1, "one", m1),
            Migration(2, "two", m2),
            Migration(3, "three", m3),
        ])
        assert runner.run_to(2) == [1, 2]
        assert order == [1, 2]
        # run_to again should do nothing
        assert runner.run_to(3) == [3]
        assert order == [1, 2, 3]

    def test_pending_after_apply(self, runner):
        def m1(c): pass
        def m2(c): pass
        runner.register_all([Migration(1, "one", m1), Migration(2, "two", m2)])
        assert len(runner.pending()) == 2
        runner.run_to(1)
        pending = runner.pending()
        assert len(pending) == 1
        assert pending[0].version == 2

    def test_reset(self, runner):
        def m1(c): pass
        runner.register(Migration(1, "one", m1))
        runner.run_all()
        assert runner.applied_versions() == [1]
        runner.reset()
        assert runner.applied_versions() == []

    def test_migration_failure_rollback(self, conn):
        """A failing migration should not mark itself as applied."""
        runner = MigrationRunner(conn)

        def good(c):
            c.execute("CREATE TABLE IF NOT EXISTS good (id INTEGER)")

        def bad(c):
            c.execute("CREATE TABLE IF NOT EXISTS bad (id INTEGER)")
            raise RuntimeError("boom")

        runner.register_all([
            Migration(1, "good", good),
            Migration(2, "bad", bad),
            Migration(3, "also_good", lambda c: None),
        ])

        with pytest.raises(RuntimeError, match="boom"):
            runner.run_all()

        # Good should be applied, bad should NOT
        assert runner.applied_versions() == [1]


class TestBuiltinMigrations:
    """Tests for built-in migrations registered with StorageEngine."""

    def test_builtin_list_not_empty(self):
        migrations = get_builtin_migrations()
        assert len(migrations) >= 1
        assert migrations[0].version == 1
        assert migrations[0].name == "initial_schema"

    def test_builtin_migration_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db))
            # Run the built-in migration manually
            get_builtin_migrations()[0].apply_fn(conn)
            # Verify kv_store exists
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='kv_store'"
            ).fetchone()
            assert tables is not None
            conn.execute(
                "INSERT INTO kv_store (namespace, key, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("ns", "k", '"v"', "now", "now"),
            )
            row = conn.execute("SELECT value FROM kv_store WHERE namespace='ns' AND key='k'").fetchone()
            assert row is not None
            conn.close()


class TestStorageEngineMigrations:
    """Verify StorageEngine auto-runs migrations on connect."""

    def test_storage_engine_applies_migrations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            s = StorageEngine(db)
            assert s.migration_runner is not None
            applied = s.migration_runner.applied_versions()
            assert 1 in applied  # initial_schema
            s.close()

    def test_migration_only_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            s1 = StorageEngine(db)
            assert s1.migration_runner.applied_versions() == [1]
            s1.close()

            # Second connection: no new migrations
            s2 = StorageEngine(db)
            assert s2.migration_runner.applied_versions() == [1]
            s2.close()

    def test_custom_migration_via_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            s = StorageEngine(db)

            applied = []

            def my_migration(c):
                applied.append(42)
                c.execute("CREATE TABLE IF NOT EXISTS my_table (id INTEGER)")

            s.migration_runner.register(Migration(42, "custom", my_migration))
            new = s.migration_runner.run_all()
            assert new == [42]
            assert applied == [42]

            # Verify table exists
            row = s._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='my_table'"
            ).fetchone()
            assert row is not None
            s.close()
