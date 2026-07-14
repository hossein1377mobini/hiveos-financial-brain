"""Tests for HiveOS Domain Manager."""

import os
import tempfile
import pytest
from pathlib import Path

from hiveos.domain.manager import DomainManager, DomainInfo


def _create_fake_domain(root: Path, name: str, agents: int = 2):
    """Helper: scaffold a minimal domain directory."""
    d = root / name
    (d / "agents" / "blueprints").mkdir(parents=True)
    (d / "flows").mkdir(parents=True)
    (d / "knowledge").mkdir(parents=True)

    domain_yaml = f"""domain:
  name: "{name}"
  version: "1.0.0-test"
  label:
    fa: "برچسب"
    en: "{name.title()}"
  description:
    en: "A test domain for {name}"
  orchestrator_agent: "orchestrator-1"
  metadata:
    tags: ["test", "{name}"]
  agents:"""
    for i in range(agents):
        role = "orchestrator" if i < 1 else "specialist"
        domain_yaml += f"""
    - id: agent-{i}
      label:
        en: "Agent {i}"
      type: {role}
      covers: ["X{i}"]
      skills:
        - skill-{i}"""
    domain_yaml += """
  flows:
    - id: flow-1
      label:
        en: "Flow 1"
      file: "flows/flow-1.yaml"
  knowledge_tree: "knowledge/tree.yaml"
"""
    (d / "domain.yaml").write_text(domain_yaml, encoding="utf-8")
    (d / "knowledge" / "tree.yaml").write_text(
        f"version: '1.0.0'\ndomain: {name}\nlabel:\n  en: Knowledge Tree\nnodes: {{}}\n",
        encoding="utf-8",
    )
    (d / "flows" / "flow-1.yaml").write_text("name: Flow 1\n", encoding="utf-8")
    return d


class TestDomainInfo:
    """Read-only domain info tests."""

    @pytest.fixture
    def domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _create_fake_domain(root, "testdom", agents=3)
            data = root / "testdom" / "domain.yaml"
            import yaml
            manifest = yaml.safe_load(data.read_text(encoding="utf-8"))
            yield DomainInfo(root / "testdom", manifest)

    def test_basic_properties(self, domain):
        assert domain.name == "testdom"
        assert domain.version == "1.0.0-test"
        assert domain.label_en == "Testdom"
        assert domain.label_fa == "برچسب"
        assert domain.orchestrator_agent == "orchestrator-1"
        assert "test" in domain.tags

    def test_agent_counts(self, domain):
        assert domain.total_agents == 3
        assert domain.orchestrator_count == 1
        assert domain.specialist_count == 2

    def test_flow_counts(self, domain):
        assert domain.total_flows == 1

    def test_knowledge_tree_count(self, domain):
        assert domain.knowledge_tree_node_count() == 0  # empty nodes dict

    def test_to_dict(self, domain):
        d = domain.to_dict()
        assert d["name"] == "testdom"
        assert d["total_agents"] == 3
        assert d["total_flows"] == 1
        assert len(d["agents"]) == 3


class TestDomainManager:
    """DomainManager lifecycle tests."""

    @pytest.fixture
    def mgr(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield DomainManager(Path(tmp))

    def test_list_empty(self, mgr):
        assert mgr.list_domains() == []

    def test_list_with_domains(self, mgr):
        _create_fake_domain(mgr._root, "alpha")
        _create_fake_domain(mgr._root, "beta", agents=5)
        domains = mgr.list_domains()
        assert len(domains) == 2
        names = sorted(d.name for d in domains)
        assert names == ["alpha", "beta"]

    def test_get_domain_exists(self, mgr):
        _create_fake_domain(mgr._root, "gamma")
        d = mgr.get_domain("gamma")
        assert d is not None
        assert d.name == "gamma"

    def test_get_domain_not_found(self, mgr):
        assert mgr.get_domain("nope") is None

    def test_get_agent_blueprint_path(self, mgr):
        _create_fake_domain(mgr._root, "testdom")
        # Create the actual blueprint file
        bp_dir = mgr._root / "testdom" / "agents" / "blueprints"
        bp_dir.mkdir(parents=True, exist_ok=True)
        bp_file = bp_dir / "agent-0.yaml"
        bp_file.write_text("agent_id: agent-0\n", encoding="utf-8")
        path = mgr.get_agent_blueprint_path("testdom", "agent-0")
        assert path is not None
        assert path.exists()

    def test_get_agent_blueprint_unknown(self, mgr):
        _create_fake_domain(mgr._root, "testdom")
        assert mgr.get_agent_blueprint_path("testdom", "nonexistent") is None

    def test_get_flow_path(self, mgr):
        _create_fake_domain(mgr._root, "testdom")
        path = mgr.get_flow_path("testdom", "flow-1")
        assert path is not None
        assert path.exists()

    def test_get_flow_path_unknown(self, mgr):
        _create_fake_domain(mgr._root, "testdom")
        assert mgr.get_flow_path("testdom", "nonexistent") is None

    def test_install(self, mgr):
        # Create a domain outside the manager's root
        with tempfile.TemporaryDirectory() as tmp:
            src = _create_fake_domain(Path(tmp), "external")
            d = mgr.install(src)
            assert d.name == "external"
            assert d.version == "1.0.0-test"
            # Should now appear in list
            assert len(mgr.list_domains()) == 1

    def test_install_duplicate(self, mgr):
        with tempfile.TemporaryDirectory() as tmp:
            src = _create_fake_domain(Path(tmp), "dup")
            mgr.install(src)
            with pytest.raises(FileExistsError):
                mgr.install(src)

    def test_install_invalid_source(self, mgr):
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid"
            invalid.mkdir()
            with pytest.raises(ValueError):
                mgr.install(invalid)

    def test_remove(self, mgr):
        _create_fake_domain(mgr._root, "toremove")
        assert len(mgr.list_domains()) == 1
        mgr.remove("toremove", permanent=True)  # permanent to actually delete the dir
        assert len(mgr.list_domains()) == 0

    def test_remove_nonexistent(self, mgr):
        with pytest.raises(KeyError):
            mgr.remove("ghost")

    def test_remove_permanent(self, mgr):
        _create_fake_domain(mgr._root, "temp")
        d = mgr.get_domain("temp")
        assert d is not None
        assert d.root.exists()
        mgr.remove("temp", permanent=True)
        assert not d.root.exists()

    def test_refresh(self, mgr):
        _create_fake_domain(mgr._root, "dom1")
        mgr.list_domains()  # cache built
        assert len(mgr._cache) == 1
        _create_fake_domain(mgr._root, "dom2")
        mgr.refresh()
        assert len(mgr._cache) == 2
