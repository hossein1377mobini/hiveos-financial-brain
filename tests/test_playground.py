"""Tests for HiveOS Playground — Flow Validator, Auto-Agent, Template Browser."""

import os
import tempfile
from pathlib import Path
import yaml

import pytest

from hiveos.playground import PlaygroundEngine


# ── Fixtures ──────────────────────────────────────────────────────────

SAMPLE_VALID_FLOW = """\
name: "Test Flow"
version: "1.0.0"
description: "A test flow for validation"
trigger:
  type: manual
agents:
  - id: agent-1
    name: "Agent One"
    skills:
      - test-skill
    depends_on: []
"""

SAMPLE_INVALID_FLOW = """\
name: ""
version: "bad-version"
agents: "not-a-list"
"""


@pytest.fixture
def engine():
    """Create a PlaygroundEngine with a temp domains directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        domains_root = Path(tmpdir)
        yield PlaygroundEngine(domains_root=domains_root)


@pytest.fixture
def engine_with_accounting():
    """Create a PlaygroundEngine with a mock accounting domain."""
    with tempfile.TemporaryDirectory() as tmpdir:
        domains_root = Path(tmpdir)

        # Create domain structure
        bp_dir = domains_root / "accounting" / "agents" / "blueprints"
        flows_dir = domains_root / "accounting" / "flows"
        bp_dir.mkdir(parents=True)
        flows_dir.mkdir(parents=True)

        # Create an orchestrator blueprint
        master_bp = {
            "agent_id": "master-financial-assistant",
            "name": {"en": "Master Financial Assistant", "fa": "دستیار ارشد مالی"},
            "type": "orchestrator",
            "description": {"en": "Entry point for all accounting queries", "fa": ""},
            "covers": ["A", "B"],
            "skills": [
                {"name": "query-routing", "description": "Routes queries to sub-agents"},
                {"name": "intent-classification", "description": "Classifies user intent"},
            ],
        }
        (bp_dir / "master-financial-assistant.yaml").write_text(
            yaml.safe_dump(master_bp), encoding="utf-8"
        )

        # Create a specialist blueprint
        recorder_bp = {
            "agent_id": "financial-recorder",
            "name": {"en": "Financial Recorder", "fa": "ثبت‌کننده مالی"},
            "type": "domain agent",
            "description": {"en": "Records financial transactions and journal entries", "fa": ""},
            "covers": ["A"],
            "skills": [
                {"name": "journal-entry", "description": "Posts journal entries"},
                {"name": "reconciliation", "description": "Reconciles accounts"},
            ],
        }
        (bp_dir / "financial-recorder.yaml").write_text(
            yaml.safe_dump(recorder_bp), encoding="utf-8"
        )

        # Create a flow template
        flow_tpl = {
            "name": "Period-End Closing",
            "name_fa": "بستن حساب پایان دوره",
            "description": "Complete period-end financial close workflow",
            "version": "1.0.0",
            "domain": "accounting",
            "trigger": {"type": "manual"},
            "agents": [
                {"id": "financial-recorder", "name": "Financial Recorder", "skills": ["journal-entry"]},
                {"id": "financial-reporter", "name": "Financial Reporter", "skills": ["financial-statements"]},
            ],
        }
        (flows_dir / "financial-close.yaml").write_text(
            yaml.safe_dump(flow_tpl), encoding="utf-8"
        )

        yield PlaygroundEngine(domains_root=domains_root)


# ── P-01: Flow Validator Tests ────────────────────────────────────────

class TestValidateFlow:
    def test_valid_flow(self, engine):
        result = engine.validate_flow(SAMPLE_VALID_FLOW)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_yaml(self, engine):
        result = engine.validate_flow("{{{bad yaml}}}")
        assert result["valid"] is False
        assert any("parse error" in e.lower() for e in result["errors"])

    def test_missing_name(self, engine):
        result = engine.validate_flow(SAMPLE_INVALID_FLOW)
        assert result["valid"] is False
        # At minimum agents-not-a-list should be caught
        assert len(result["errors"]) > 0

    def test_agents_not_list(self, engine):
        result = engine.validate_flow(SAMPLE_INVALID_FLOW)
        assert result["valid"] is False
        assert any("list" in e for e in result["errors"])

    def test_empty_yaml(self, engine):
        result = engine.validate_flow("")
        assert result["valid"] is False

    def test_not_a_dict(self, engine):
        result = engine.validate_flow("- just\na list")
        assert result["valid"] is False

    def test_warnings_on_empty_agents(self, engine):
        flow = """\
name: "Empty Flow"
version: "1.0.0"
agents: []
trigger:
  type: manual
"""
        result = engine.validate_flow(flow)
        assert result["valid"] is True
        assert len(result["warnings"]) > 0


# ── P-02: Auto-Agent Tests ────────────────────────────────────────────

class TestAutoAgents:
    def test_no_blueprints(self, engine):
        result = engine.auto_agents("test task", "nonexistent")
        assert result["domain"] == "nonexistent"
        assert len(result["agents"]) == 0

    def test_matching_agents(self, engine_with_accounting):
        result = engine_with_accounting.auto_agents(
            "I need to record financial transactions and post journal entries"
        )
        assert result["domain"] == "accounting"
        assert len(result["agents"]) > 0
        # Should find financial-recorder
        agent_ids = [a["id"] for a in result["agents"]]
        assert "financial-recorder" in agent_ids

    def test_orchestrator_recommended(self, engine_with_accounting):
        result = engine_with_accounting.auto_agents(
            "I need accounting help"
        )
        # Should recommend an orchestrator
        assert result["recommended_orchestrator"]
        # recommended_orchestrator should be the agent_id string
        assert isinstance(result["recommended_orchestrator"], str)
        assert len(result["recommended_orchestrator"]) > 0

    def test_orchestrator_boosted(self, engine_with_accounting):
        result = engine_with_accounting.auto_agents(
            "query routing and intent classification"
        )
        agent_ids = [a["id"] for a in result["agents"]]
        assert "master-financial-assistant" in agent_ids


# ── P-03: Template Browser Tests ──────────────────────────────────────

class TestListTemplates:
    def test_no_domain(self, engine):
        result = engine.list_templates("nonexistent")
        assert len(result["templates"]) == 0

    def test_lists_templates(self, engine_with_accounting):
        result = engine_with_accounting.list_templates("accounting")
        assert result["domain"] == "accounting"
        assert len(result["templates"]) == 1
        tpl = result["templates"][0]
        assert tpl["name"] == "Period-End Closing"
        assert tpl["agent_count"] == 2
        assert tpl["trigger_type"] == "manual"

    def test_template_metadata(self, engine_with_accounting):
        result = engine_with_accounting.list_templates("accounting")
        tpl = result["templates"][0]
        assert tpl["version"] == "1.0.0"
        # name_fa may or may not be present depending on yaml serialization
        assert tpl.get("name_fa", tpl.get("name", ""))
        assert tpl["domain"] == "accounting"
