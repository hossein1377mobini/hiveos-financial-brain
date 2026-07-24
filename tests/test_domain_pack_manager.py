"""Comprehensive tests for the Domain Pack Manager."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml

from hiveos.domain_pack.loader import load_pack
from hiveos.domain_pack.manager import DomainPackError, DomainPackManager
from hiveos.domain_pack.models import (
    DomainPackMetadata,
    SkillDefinition,
    WorkflowDefinition,
)
from hiveos.domain_pack.registry import DomainPackRegistry
from hiveos.domain_pack.validator import validate_pack, validate_pack_dry_run
from hiveos.storage import StorageEngine


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_storage(tmp_path: Path) -> StorageEngine:
    db_path = tmp_path / "test.db"
    return StorageEngine(db_path=db_path)


def _create_valid_pack(tmp_path: Path, pack_id: str = "test-domain", version: str = "1.0.0") -> Path:
    """Create a fully valid domain pack directory."""
    pack_dir = tmp_path / pack_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    # domain.yaml
    manifest = {
        "id": pack_id,
        "version": version,
        "name": f"{pack_id.title()} Pack",
        "description": f"A test domain pack ({pack_id})",
        "min_core_version": "1.0.0",
        "author": {"name": "Test Author", "url": "https://example.com"},
        "skills": [
            {"id": "test-skill-a"},
            {"id": "test-skill-b"},
        ],
        "workflows": [
            {"id": "test-workflow"},
        ],
    }
    (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

    # knowledge/
    knowledge_dir = pack_dir / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "01-basics.md").write_text("# Basics\nSome knowledge.", encoding="utf-8")
    (knowledge_dir / "02-advanced.md").write_text("# Advanced\nMore knowledge.", encoding="utf-8")

    # skills/
    skills_dir = pack_dir / "skills"
    skills_dir.mkdir()
    for skill_id in ["test-skill-a", "test-skill-b"]:
        skill_data = {
            "id": skill_id,
            "name": skill_id.replace("-", " ").title(),
            "version": "1.0.0",
            "description": f"Test skill {skill_id}",
            "input_schema": {"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]},
            "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]},
            "instruction": f"You are the {skill_id} assistant.",
            "required_capabilities": ["knowledge_search"],
            "model": {"provider": "default", "temperature": 0.3},
        }
        (skills_dir / f"{skill_id}.yaml").write_text(yaml.dump(skill_data), encoding="utf-8")

    # workflows/
    workflows_dir = pack_dir / "workflows"
    workflows_dir.mkdir()
    workflow_data = {
        "id": "test-workflow",
        "name": "Test Workflow",
        "description": "A test workflow",
        "steps": [
            {
                "id": "step-a",
                "skill_id": "test-skill-a",
                "input_mapping": {"input": "$.input.data"},
            },
            {
                "id": "step-b",
                "skill_id": "test-skill-b",
                "input_mapping": {"input": "$.steps.step-a.output.result"},
            },
        ],
    }
    (workflows_dir / "test-workflow.yaml").write_text(yaml.dump(workflow_data), encoding="utf-8")

    return pack_dir


# ── Validator tests ─────────────────────────────────────────────────────────


class TestValidator:
    def test_valid_pack_passes(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        errors = validate_pack(pack_dir)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_domain_yaml(self, tmp_path):
        pack_dir = tmp_path / "empty-pack"
        pack_dir.mkdir()
        errors = validate_pack(pack_dir)
        assert any("domain.yaml" in e for e in errors)

    def test_invalid_yaml(self, tmp_path):
        pack_dir = tmp_path / "bad-yaml"
        pack_dir.mkdir()
        (pack_dir / "domain.yaml").write_text(": : invalid yaml [", encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("Invalid YAML" in e or "mapping" in e for e in errors)

    def test_missing_required_fields(self, tmp_path):
        pack_dir = tmp_path / "incomplete"
        pack_dir.mkdir()
        manifest = {"id": "incomplete"}  # missing version, name, description, etc.
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("missing required field" in e.lower() for e in errors)

    def test_invalid_id_format(self, tmp_path):
        pack_dir = tmp_path / "bad-id"
        pack_dir.mkdir()
        manifest = {
            "id": "UPPERCASE_ILLEGAL!!",
            "version": "1.0.0",
            "name": "Bad ID",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("ID" in e and "lowercase" in e for e in errors)

    def test_invalid_version(self, tmp_path):
        pack_dir = tmp_path / "bad-ver"
        pack_dir.mkdir()
        manifest = {
            "id": "bad-ver",
            "version": "not-semver",
            "name": "Bad Version",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("semver" in e for e in errors)

    def test_min_core_version_too_high(self, tmp_path):
        pack_dir = tmp_path / "core-too-high"
        pack_dir.mkdir()
        manifest = {
            "id": "core-too-high",
            "version": "1.0.0",
            "name": "Core Too High",
            "description": "test",
            "min_core_version": "99.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir, core_version="1.0.0")
        assert any("min_core_version" in e.lower() or "requires core" in e for e in errors)

    def test_missing_knowledge_dir(self, tmp_path):
        pack_dir = tmp_path / "no-knowledge"
        pack_dir.mkdir()
        manifest = {
            "id": "no-knowledge",
            "version": "1.0.0",
            "name": "No Knowledge",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("knowledge/" in e for e in errors)

    def test_empty_knowledge_dir(self, tmp_path):
        pack_dir = tmp_path / "empty-knowledge"
        pack_dir.mkdir()
        (pack_dir / "knowledge").mkdir()
        manifest = {
            "id": "empty-knowledge",
            "version": "1.0.0",
            "name": "Empty Knowledge",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("empty" in e.lower() for e in errors)

    def test_missing_skills_dir(self, tmp_path):
        pack_dir = tmp_path / "no-skills"
        pack_dir.mkdir()
        (pack_dir / "knowledge").mkdir()
        (pack_dir / "knowledge" / "doc.md").write_text("# Doc", encoding="utf-8")
        manifest = {
            "id": "no-skills",
            "version": "1.0.0",
            "name": "No Skills",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("skills/" in e for e in errors)

    def test_missing_skill_file(self, tmp_path):
        pack_dir = tmp_path / "missing-skill"
        pack_dir.mkdir()
        (pack_dir / "knowledge").mkdir()
        (pack_dir / "knowledge" / "doc.md").write_text("# Doc", encoding="utf-8")
        (pack_dir / "skills").mkdir()
        manifest = {
            "id": "missing-skill",
            "version": "1.0.0",
            "name": "Missing Skill",
            "description": "test",
            "min_core_version": "1.0.0",
            "skills": [{"id": "nonexistent-skill"}],
        }
        (pack_dir / "domain.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("nonexistent-skill" in e for e in errors)

    def test_executable_file_rejected(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        # Drop a .py file into skills/
        (pack_dir / "skills" / "malicious.py").write_text("import os; os.system('rm -rf /')", encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("Executable" in e and "malicious.py" in e for e in errors)

    def test_executable_in_knowledge_rejected(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        (pack_dir / "knowledge" / "evil.sh").write_text("#!/bin/bash\nevil", encoding="utf-8")
        errors = validate_pack(pack_dir)
        assert any("Executable" in e and "evil.sh" in e for e in errors)

    def test_dry_run(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        is_valid, errors = validate_pack_dry_run(pack_dir)
        assert is_valid is True
        assert errors == []

    def test_dry_run_invalid(self, tmp_path):
        pack_dir = tmp_path / "bad"
        pack_dir.mkdir()
        is_valid, errors = validate_pack_dry_run(pack_dir)
        assert is_valid is False
        assert len(errors) > 0


# ── Loader tests ────────────────────────────────────────────────────────────


class TestLoader:
    def test_load_valid_pack(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        meta = load_pack(pack_dir)
        assert meta.id == "test-domain"
        assert meta.version == "1.0.0"
        assert len(meta.skills) == 2
        assert len(meta.workflows) == 1

    def test_skill_fields_loaded(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        meta = load_pack(pack_dir)
        skill = meta.skills[0]
        assert skill.id in ("test-skill-a", "test-skill-b")
        assert skill.name
        assert skill.instruction
        assert skill.pack_id == "test-domain"

    def test_workflow_steps_loaded(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        meta = load_pack(pack_dir)
        wf = meta.workflows[0]
        assert wf.id == "test-workflow"
        assert len(wf.steps) == 2
        assert wf.steps[0].skill_id == "test-skill-a"
        assert wf.pack_id == "test-domain"


# ── Manager tests ───────────────────────────────────────────────────────────


class TestDomainPackManager:
    def _make_manager(self, tmp_path: Path) -> DomainPackManager:
        storage = _make_storage(tmp_path / "db")
        base_dir = tmp_path / "domains"
        return DomainPackManager(base_dir=base_dir, storage=storage)

    def test_install_valid_pack(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)

        meta = asyncio.run(mgr.install(pack_dir))
        assert meta.id == "test-domain"
        assert meta.version == "1.0.0"
        assert meta.enabled is True

    def test_list_installed(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        installed = asyncio.run(mgr.list_installed())
        assert len(installed) == 1
        assert installed[0].id == "test-domain"

    def test_get_pack(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        meta = asyncio.run(mgr.get_pack("test-domain"))
        assert meta.id == "test-domain"

    def test_get_pack_not_found(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        with pytest.raises(DomainPackError, match="not installed"):
            asyncio.run(mgr.get_pack("nonexistent"))

    def test_enable_disable(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        asyncio.run(mgr.disable("test-domain"))
        packs = asyncio.run(mgr.list_installed())
        assert packs[0].enabled is False

        asyncio.run(mgr.enable("test-domain"))
        packs = asyncio.run(mgr.list_installed())
        assert packs[0].enabled is True

    def test_remove(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        result = asyncio.run(mgr.remove("test-domain"))
        assert result is True

        installed = asyncio.run(mgr.list_installed())
        assert len(installed) == 0

    def test_remove_not_installed(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        with pytest.raises(DomainPackError, match="not installed"):
            asyncio.run(mgr.remove("nonexistent"))

    def test_duplicate_install_rejected(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        with pytest.raises(DomainPackError, match="already installed"):
            asyncio.run(mgr.install(pack_dir))

    def test_get_skill_cross_pack(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        skill = asyncio.run(mgr.get_skill("test-skill-a"))
        assert skill is not None
        assert skill.id == "test-skill-a"
        assert skill.pack_id == "test-domain"

    def test_get_skill_not_found(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        skill = asyncio.run(mgr.get_skill("nonexistent"))
        assert skill is None

    def test_get_workflow(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        wf = asyncio.run(mgr.get_workflow("test-workflow"))
        assert wf is not None
        assert wf.id == "test-workflow"

    def test_list_skills(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        skills = asyncio.run(mgr.list_skills())
        assert len(skills) == 2

    def test_list_skills_by_pack(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        skills = asyncio.run(mgr.list_skills(pack_id="test-domain"))
        assert len(skills) == 2

        skills = asyncio.run(mgr.list_skills(pack_id="other"))
        assert len(skills) == 0

    def test_list_workflows(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        wfs = asyncio.run(mgr.list_workflows())
        assert len(wfs) == 1

    def test_update_pack(self, tmp_path):
        pack_dir_v1 = _create_valid_pack(tmp_path, version="1.0.0")
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir_v1))

        # Create v2
        pack_dir_v2 = _create_valid_pack(tmp_path / "v2", pack_id="test-domain", version="2.0.0")

        updated = asyncio.run(mgr.update("test-domain", pack_dir_v2))
        assert updated.version == "2.0.0"

    def test_update_wrong_id(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path, pack_id="pack-a")
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        pack_dir_b = _create_valid_pack(tmp_path / "b", pack_id="pack-b")
        with pytest.raises(DomainPackError, match="does not match"):
            asyncio.run(mgr.update("pack-a", pack_dir_b))

    def test_install_invalid_pack(self, tmp_path):
        bad_dir = tmp_path / "bad"
        bad_dir.mkdir()
        mgr = self._make_manager(tmp_path)
        with pytest.raises(DomainPackError, match="validation failed"):
            asyncio.run(mgr.install(bad_dir))

    def test_disabled_pack_skills_excluded(self, tmp_path):
        pack_dir = _create_valid_pack(tmp_path)
        mgr = self._make_manager(tmp_path)
        asyncio.run(mgr.install(pack_dir))

        asyncio.run(mgr.disable("test-domain"))
        skills = asyncio.run(mgr.list_skills())
        assert len(skills) == 0

        skill = asyncio.run(mgr.get_skill("test-skill-a"))
        assert skill is None


# ── Registry tests ──────────────────────────────────────────────────────────


class TestRegistry:
    def test_register_and_get(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)

        meta = DomainPackMetadata(
            id="test",
            version="1.0.0",
            name="Test",
            description="Test pack",
            install_path="/tmp/test",
            installed_at="2026-01-01T00:00:00",
            enabled=True,
        )
        reg.register(meta)

        entry = reg.get("test")
        assert entry is not None
        assert entry["id"] == "test"
        assert entry["enabled"] is True

    def test_unregister(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)

        meta = DomainPackMetadata(
            id="test", version="1.0.0", name="Test", description=""
        )
        reg.register(meta)
        assert reg.unregister("test") is True
        assert reg.get("test") is None

    def test_unregister_not_found(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)
        assert reg.unregister("ghost") is False

    def test_list_all(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)

        for i in range(3):
            meta = DomainPackMetadata(
                id=f"pack-{i}", version="1.0.0", name=f"Pack {i}", description=""
            )
            reg.register(meta)

        all_packs = reg.list_all()
        assert len(all_packs) == 3

    def test_set_enabled(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)

        meta = DomainPackMetadata(
            id="test", version="1.0.0", name="Test", description=""
        )
        reg.register(meta)

        assert reg.set_enabled("test", False) is True
        assert reg.is_enabled("test") is False

        assert reg.set_enabled("test", True) is True
        assert reg.is_enabled("test") is True

    def test_set_enabled_not_found(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)
        assert reg.set_enabled("ghost", False) is False

    def test_is_installed(self, tmp_path):
        storage = _make_storage(tmp_path)
        reg = DomainPackRegistry(storage)
        assert reg.is_installed("test") is False

        meta = DomainPackMetadata(
            id="test", version="1.0.0", name="Test", description=""
        )
        reg.register(meta)
        assert reg.is_installed("test") is True
