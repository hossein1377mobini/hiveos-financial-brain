"""Playground Core API module for HiveOS.

Provides an interactive engine for flow development, validation,
and agent discovery within the HiveOS multi-agent ecosystem.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from hiveos.dsl import FlowDSL


class PlaygroundEngine:
    """Core playground engine for flow development and agent discovery.

    Provides three primary capabilities:
      - validate_flow() — validates flow YAML against the FlowDSL schema
      - auto_agents()  — keyword-based agent discovery from blueprints
      - list_templates() — enumerate available flow templates in a domain
    """

    def __init__(self, domains_root: Optional[str] = None):
        """Initialize the playground engine.

        Args:
            domains_root: Path to the HiveOS domains directory. If *None*,
                          resolves to ``<project_root>/domains/`` relative to
                          this source file's location.
        """
        if domains_root is None:
            # Walk up from src/hiveos/playground/playground.py
            # → src/hiveos/playground/ → src/hiveos/ → src/ → project root
            self.domains_root = (
                Path(__file__).resolve().parent.parent.parent.parent / "domains"
            )
        else:
            self.domains_root = Path(domains_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_flow(self, yaml_content: str) -> Dict[str, Any]:
        """Validate a flow definition expressed as YAML.

        Returns a dict with keys ``valid`` (bool), ``errors`` (list of str),
        and ``warnings`` (list of str).

        Processing steps:
        1. Parse *yaml_content* with ``yaml.safe_load``.
        2. Call ``FlowDSL.validate_structure`` on the parsed dict.
        3. Emit heuristic warnings for common omissions.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Step 1 — raw YAML parse
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:
            errors.append(f"YAML parse error: {exc}")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if not isinstance(data, dict):
            errors.append("YAML content must parse to a dictionary (flow definition)")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Step 2 — FlowDSL structure validation
        dsl_errors = FlowDSL.validate_structure(data)
        errors.extend(dsl_errors)

        # Step 3 — heuristic warnings
        if "description" not in data or not data.get("description"):
            warnings.append("Flow has no description; consider adding one for clarity")

        if "domain" not in data or not data.get("domain"):
            warnings.append(
                "Flow has no domain specified; consider adding a 'domain' field"
            )

        trigger = data.get("trigger", {})
        if isinstance(trigger, dict):
            trig_type = trigger.get("type", "")
            if trig_type == "cron" and not trigger.get("pattern") and not trigger.get("cron"):
                warnings.append("Cron trigger has no schedule pattern")
            elif not trig_type:
                warnings.append("Trigger has no type specified; defaulting to 'manual'")
        elif trigger is None:
            warnings.append("Trigger is null; defaulting to 'manual'")

        agents = data.get("agents", [])
        if isinstance(agents, list):
            seen_ids: set = set()
            for idx, agent in enumerate(agents):
                if isinstance(agent, dict):
                    aid = agent.get("id", "")
                    if aid and aid in seen_ids:
                        warnings.append(f"Duplicate agent id '{aid}' at index {idx}")
                    seen_ids.add(aid)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def auto_agents(
        self, task_description: str, domain_name: str = "accounting"
    ) -> Dict[str, Any]:
        """Find the best-matching agent blueprints for a natural-language task.

        Scans ``domains/<domain_name>/agents/blueprints/`` and scores each
        blueprint by keyword overlap with *task_description*.

        Returns a dict with:
        - ``task`` — the original task description
        - ``domain`` — the searched domain
        - ``agents`` — ranked list of ``{id, name, match_score, type}``
        - ``recommended_orchestrator`` — the highest-scoring orchestrator
          agent, or ``None`` if none exist.
        """
        task_tokens = self._tokenize(task_description)

        blueprints_dir = self.domains_root / domain_name / "agents" / "blueprints"

        scored_agents: List[Dict[str, Any]] = []
        orchestrator_agents: List[Dict[str, Any]] = []

        if not blueprints_dir.is_dir():
            return self._empty_agents_response(task_description, domain_name)

        for blueprint_path in sorted(blueprints_dir.glob("*.yaml")):
            bp = self._load_yaml(blueprint_path)
            if not isinstance(bp, dict):
                continue

            agent_id = bp.get("agent_id", "")
            agent_type = str(bp.get("type", "specialist"))

            name_en = self._extract_localized(bp, "name", "en")
            desc_en = self._extract_localized(bp, "description", "en")
            covers = bp.get("covers", []) or []
            skill_names = self._extract_skill_names(bp.get("skills", []) or [])

            agent_text = f"{name_en} {desc_en} {' '.join(skill_names)} {' '.join(covers)}"
            agent_tokens = self._tokenize(agent_text)
            name_tokens = self._tokenize(name_en)

            if not agent_tokens:
                continue

            matching_tokens = task_tokens & agent_tokens
            name_matching_tokens = task_tokens & name_tokens

            text_ratio = len(matching_tokens) / len(agent_tokens)
            name_ratio = (
                len(name_matching_tokens) / len(name_tokens) if name_tokens else 0.0
            )

            score = round(text_ratio * 0.7 + name_ratio * 0.3, 4)

            entry = {
                "id": agent_id,
                "name": name_en,
                "match_score": score,
                "type": agent_type,
            }
            scored_agents.append(entry)
            if agent_type == "orchestrator":
                orchestrator_agents.append(entry)

        scored_agents.sort(key=lambda a: a["match_score"], reverse=True)
        orchestrator_agents.sort(key=lambda a: a["match_score"], reverse=True)

        return {
            "task": task_description,
            "domain": domain_name,
            "agents": scored_agents,
            "recommended_orchestrator": orchestrator_agents[0]["id"]
            if orchestrator_agents
            else "",
        }

    def list_templates(self, domain_name: str = "accounting") -> Dict[str, Any]:
        """List every flow template defined in the given domain.

        Reads ``domains/<domain_name>/flows/*.yaml`` and extracts metadata
        from each.

        Returns a dict with:
        - ``domain`` — the queried domain
        - ``templates`` — list of ``{filename, name, description, version,
          trigger_type, agent_count}``
        """
        flows_dir = self.domains_root / domain_name / "flows"
        templates: List[Dict[str, Any]] = []

        if not flows_dir.is_dir():
            return {"domain": domain_name, "templates": []}

        for flow_path in sorted(flows_dir.glob("*.yaml")):
            data = self._load_yaml(flow_path)
            if not isinstance(data, dict):
                continue

            trigger = data.get("trigger", {})
            trigger_type = (
                trigger.get("type", "manual") if isinstance(trigger, dict) else "manual"
            )

            agents = data.get("agents", [])
            agent_count = len(agents) if isinstance(agents, list) else 0

            templates.append(
                {
                    "filename": flow_path.name,
                    "name": data.get("name", flow_path.stem),
                    "name_fa": data.get("name_fa", ""),
                    "description": data.get("description", ""),
                    "version": data.get("version", "0.0.0"),
                    "domain": data.get("domain", domain_name),
                    "trigger_type": trigger_type,
                    "agent_count": agent_count,
                    "agent_ids": [
                        a.get("id", "") for a in agents
                    ] if isinstance(agents, list) else [],
                }
            )

        return {"domain": domain_name, "templates": templates}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> set:
        """Split *text* into a set of lowercase alphanumeric tokens.

        Words joined by ``-`` or ``_`` are kept as single tokens
        (e.g. ``financial-recorder`` stays intact).
        """
        return set(re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", text.lower()))

    @staticmethod
    def _load_yaml(path: Path) -> Any:
        """Safely load a YAML file, returning ``None`` on failure."""
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def _extract_localized(
        data: dict, field: str, lang: str, default: str = ""
    ) -> str:
        """Extract a possibly-localised string field.

        If *field* is a dict with *lang* as a key, return that value.
        Otherwise coerce the value to a string or return *default*.
        """
        val = data.get(field, default)
        if isinstance(val, dict):
            return str(val.get(lang, default))
        return str(val) if val else default

    @staticmethod
    def _extract_skill_names(skills: list) -> List[str]:
        """Extract display-name strings from a skill list.

        Handles both ``{"name": "...", "description": "..."}`` dict entries
        and plain strings.
        """
        names: List[str] = []
        for s in skills:
            if isinstance(s, dict):
                names.append(str(s.get("name", "")))
            else:
                names.append(str(s))
        return names

    @staticmethod
    def _empty_agents_response(
        task_description: str, domain_name: str
    ) -> Dict[str, Any]:
        """Return a stub response when the blueprints directory is absent."""
        return {
            "task": task_description,
            "domain": domain_name,
            "agents": [],
            "recommended_orchestrator": None,
        }
