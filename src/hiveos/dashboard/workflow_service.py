"""WorkflowService — find, load, save, and validate workflow YAML files.

Workflows live inside domain packs under `workflows/{id}.yaml`.
This service provides CRUD operations for editing existing workflow
templates. Full creation is deferred to V2.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from hiveos.domain_pack.loader import load_pack
from hiveos.dsl import FlowDSL


class WorkflowService:
    """Manages workflow YAML files across installed domain packs."""

    def __init__(self, domain_registry):
        self._registry = domain_registry

    # ── Lookup ─────────────────────────────────────────────────────

    def find_workflow_file(self, workflow_id: str) -> Optional[Tuple[Path, str]]:
        """Find the YAML file for *workflow_id* across all installed packs.

        Returns (file_path, pack_id) or (None, None) if not found.
        """
        installed = self._registry._get_installed()
        for pack_id, meta in installed.items():
            pack_path = Path(meta.get("path", ""))
            if not pack_path.exists():
                continue
            wf_dir = pack_path / "workflows"
            for ext in ("yaml", "yml"):
                candidate = wf_dir / f"{workflow_id}.{ext}"
                if candidate.exists():
                    return candidate, pack_id
        return None, None

    def load_workflow_yaml(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load the raw YAML dict for a workflow."""
        fpath, pack_id = self.find_workflow_file(workflow_id)
        if fpath is None:
            return None
        data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        data["_pack_id"] = pack_id
        data["_file_path"] = str(fpath)
        return data

    def load_all_workflows(self) -> List[Dict[str, Any]]:
        """Aggregate all workflows from all installed packs (full detail)."""
        results: List[Dict[str, Any]] = []
        installed = self._registry._get_installed()
        for pack_id, meta in installed.items():
            pack_path = Path(meta.get("path", ""))
            if not pack_path.exists():
                continue
            try:
                pack = load_pack(pack_path)
            except Exception:
                continue
            for wf_def in pack.workflows:
                # Load raw YAML for full detail
                raw = self.load_workflow_yaml(wf_def.id)
                if raw is None:
                    # Fallback to parsed data
                    raw = {
                        "id": wf_def.id,
                        "name": wf_def.name,
                        "description": wf_def.description,
                        "steps": [
                            {"id": s.id, "skill_id": s.skill_id, "input_mapping": s.input_mapping}
                            for s in wf_def.steps
                        ],
                    }
                    raw["_pack_id"] = pack_id
                # Strip internal fields
                entry = {k: v for k, v in raw.items() if not k.startswith("_")}
                entry["pack_id"] = pack_id
                entry["pack_name"] = pack.name
                results.append(entry)
        return results

    # ── Validate ───────────────────────────────────────────────────

    def validate_workflow(self, data: Dict[str, Any]) -> List[str]:
        """Validate a workflow YAML dict. Returns list of error strings (empty = valid)."""
        errors: List[str] = []

        # Required top-level fields
        if not data.get("name"):
            errors.append("Missing required field: 'name'")

        # Validate steps if present (simple model)
        steps = data.get("steps", [])
        if isinstance(steps, list):
            seen_step_ids: set = set()
            for idx, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"Step at index {idx} must be a dict")
                    continue
                sid = step.get("id", "")
                if not sid:
                    errors.append(f"Step at index {idx} missing 'id'")
                elif sid in seen_step_ids:
                    errors.append(f"Duplicate step id '{sid}' at index {idx}")
                seen_step_ids.add(sid)
                if not step.get("skill_id"):
                    errors.append(f"Step '{sid}' missing 'skill_id'")

        # Validate agents if present (simple model)
        agents = data.get("agents", [])
        if isinstance(agents, list):
            for idx, agent in enumerate(agents):
                if not isinstance(agent, dict):
                    errors.append(f"Agent at index {idx} must be a dict")
                    continue
                if not agent.get("id"):
                    errors.append(f"Agent at index {idx} missing 'id'")

        # Validate components if present (advanced model)
        components = data.get("components", [])
        if isinstance(components, list) and len(components) > 0:
            # Reuse FlowDSL validation
            ds_errors = FlowDSL.validate_structure(data)
            errors.extend(ds_errors)

        # Validate trigger if present
        trigger = data.get("trigger")
        if trigger and isinstance(trigger, dict):
            valid_types = {"cron", "event", "manual", "webhook"}
            ttype = trigger.get("type", "")
            if ttype and ttype not in valid_types:
                errors.append(f"Invalid trigger type: '{ttype}'. Must be one of: {', '.join(sorted(valid_types))}")

        # Validate tags
        tags = data.get("tags")
        if tags is not None and not isinstance(tags, list):
            errors.append("'tags' must be a list of strings")

        return errors

    # ── Save ───────────────────────────────────────────────────────

    def save_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Save (overwrite) a workflow YAML file.

        Returns (success, message).
        """
        fpath, pack_id = self.find_workflow_file(workflow_id)
        if fpath is None:
            return False, f"Workflow '{workflow_id}' not found in any installed pack"

        # Validate before saving
        errors = self.validate_workflow(data)
        if errors:
            return False, f"Validation errors: {'; '.join(errors)}"

        # Remove internal fields before writing
        clean = {k: v for k, v in data.items() if not k.startswith("_")}

        # Ensure the id matches
        clean["id"] = workflow_id

        try:
            yaml_str = yaml.dump(
                clean,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            )
            fpath.write_text(yaml_str, encoding="utf-8")
            return True, f"Workflow '{workflow_id}' saved to {fpath}"
        except Exception as e:
            return False, f"Failed to write YAML: {e}"

    def patch_workflow(
        self, workflow_id: str, updates: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Apply partial updates to a workflow.

        Supports editing: name, description, steps, agents, components,
        trigger, tags, deliver, memory, version.
        Returns (success, message).
        """
        current = self.load_workflow_yaml(workflow_id)
        if current is None:
            return False, f"Workflow '{workflow_id}' not found"

        # Allowed top-level edit keys
        allowed_keys = {
            "name", "description", "version", "trigger", "steps",
            "agents", "components", "tags", "deliver", "memory",
        }

        for key, value in updates.items():
            if key.startswith("_"):
                continue
            if key not in allowed_keys:
                continue  # silently skip disallowed keys
            current[key] = value

        return self.save_workflow(workflow_id, current)

    def delete_workflow(self, workflow_id: str) -> Tuple[bool, str]:
        """Delete a workflow YAML file and remove from pack manifest.

        Returns (success, message).
        """
        fpath, pack_id = self.find_workflow_file(workflow_id)
        if fpath is None:
            return False, f"Workflow '{workflow_id}' not found"

        try:
            # Back up first
            backup = fpath.with_suffix(f".yaml.bak")
            backup.write_text(fpath.read_text(encoding="utf-8"), encoding="utf-8")

            # Remove from pack manifest
            pack_path = fpath.parent.parent  # workflows/ -> pack root
            manifest_path = pack_path / "domain.yaml"
            if manifest_path.exists():
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                if isinstance(manifest, dict):
                    wf_list = manifest.get("workflows", [])
                    if isinstance(wf_list, list):
                        manifest["workflows"] = [
                            w for w in wf_list
                            if (w.get("id") if isinstance(w, dict) else str(w)) != workflow_id
                        ]
                        manifest_path.write_text(
                            yaml.dump(manifest, default_flow_style=False, allow_unicode=True, sort_keys=False),
                            encoding="utf-8",
                        )

            # Delete the workflow file
            fpath.unlink()

            return True, f"Workflow '{workflow_id}' deleted (backup at {backup})"
        except Exception as e:
            return False, f"Failed to delete workflow: {e}"

    # ── Helpers ────────────────────────────────────────────────────

    def get_component_types(self) -> List[Dict[str, Any]]:
        """Return metadata about all supported component types (for UI editors)."""
        return FlowDSL.get_component_types()

    def get_editable_fields(self) -> Dict[str, Any]:
        """Return schema describing editable fields for the UI."""
        return {
            "top_level": {
                "name": {"type": "string", "required": True, "description": "Workflow display name"},
                "description": {"type": "string", "required": False, "description": "Human-readable description"},
                "version": {"type": "string", "required": False, "description": "Semantic version"},
                "tags": {"type": "list[string]", "required": False, "description": "Tags for categorization"},
            },
            "trigger": {
                "type": {"type": "enum", "values": ["cron", "event", "manual", "webhook"]},
                "pattern": {"type": "string", "description": "Cron expression or event pattern"},
            },
            "step_fields": {
                "id": {"type": "string", "required": True},
                "skill_id": {"type": "string", "required": True},
                "input_mapping": {"type": "dict", "required": False},
            },
            "agent_fields": {
                "id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "skills": {"type": "list[string]", "required": True},
                "knowledge": {"type": "list[string]", "required": False},
                "depends_on": {"type": "list[string]", "required": False},
                "timeout": {"type": "integer", "required": False},
                "retry": {"type": "integer", "required": False},
                "action": {"type": "dict", "required": False},
            },
            "deliver": {
                "to": {"type": "string", "description": "Delivery target (origin, telegram, discord, all)"},
                "format": {"type": "string", "description": "Output format (markdown, json, text)"},
            },
        }
