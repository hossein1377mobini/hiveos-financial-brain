"""Domain Pack loader — reads a pack directory into model objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .models import (
    AuthorInfo,
    DomainPackMetadata,
    SkillDefinition,
    WorkflowDefinition,
    WorkflowStep,
)


def load_pack(pack_path: Path) -> DomainPackMetadata:
    """Load a Domain Pack from disk into a DomainPackMetadata object.

    Pre-condition: the pack has already passed validate_pack() —
    the loader trusts the structure.
    """
    manifest_path = pack_path / "domain.yaml"
    manifest: Dict[str, Any] = yaml.safe_load(
        manifest_path.read_text(encoding="utf-8")
    )

    # Parse author
    author_data = manifest.get("author", {})
    author = AuthorInfo(
        name=author_data.get("name", "") if isinstance(author_data, dict) else "",
        url=author_data.get("url", "") if isinstance(author_data, dict) else "",
    )

    # Parse skills
    skills = _load_skills(pack_path, manifest)

    # Parse workflows
    workflows = _load_workflows(pack_path, manifest)

    pack_id = manifest.get("id", pack_path.name)

    return DomainPackMetadata(
        id=pack_id,
        version=manifest.get("version", "0.0.0"),
        name=manifest.get("name", pack_id),
        description=manifest.get("description", ""),
        min_core_version=manifest.get("min_core_version", "1.0.0"),
        author=author,
        skills=skills,
        workflows=workflows,
        install_path=str(pack_path),
    )


def _load_skills(pack_path: Path, manifest: Dict[str, Any]) -> List[SkillDefinition]:
    """Load all skill YAML files referenced in manifest."""
    skills_dir = pack_path / "skills"
    skills: List[SkillDefinition] = []
    pack_id = manifest.get("id", "")

    manifest_skills = manifest.get("skills", [])
    if not isinstance(manifest_skills, list):
        return skills

    for skill_ref in manifest_skills:
        skill_id = skill_ref.get("id", "") if isinstance(skill_ref, dict) else str(skill_ref)
        if not skill_id:
            continue

        # Try .yaml then .yml
        skill_path = skills_dir / f"{skill_id}.yaml"
        if not skill_path.exists():
            skill_path = skills_dir / f"{skill_id}.yml"
            if not skill_path.exists():
                continue

        data = yaml.safe_load(skill_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue

        skills.append(
            SkillDefinition(
                id=data.get("id", skill_id),
                name=data.get("name", skill_id),
                version=data.get("version", "0.0.0"),
                description=data.get("description", ""),
                input_schema=data.get("input_schema", {}),
                output_schema=data.get("output_schema", {}),
                knowledge_requirements=data.get("knowledge_requirements", {}),
                required_capabilities=data.get("required_capabilities", []),
                model=data.get("model", {}),
                instruction=data.get("instruction", ""),
                pack_id=pack_id,
            )
        )

    return skills


def _load_workflows(
    pack_path: Path, manifest: Dict[str, Any]
) -> List[WorkflowDefinition]:
    """Load all workflow YAML files referenced in manifest."""
    workflows_dir = pack_path / "workflows"
    workflows: List[WorkflowDefinition] = []
    pack_id = manifest.get("id", "")

    manifest_workflows = manifest.get("workflows", [])
    if not isinstance(manifest_workflows, list):
        return workflows

    for wf_ref in manifest_workflows:
        wf_id = wf_ref.get("id", "") if isinstance(wf_ref, dict) else str(wf_ref)
        if not wf_id:
            continue

        wf_path = workflows_dir / f"{wf_id}.yaml"
        if not wf_path.exists():
            wf_path = workflows_dir / f"{wf_id}.yml"
            if not wf_path.exists():
                continue

        data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue

        # Parse steps
        steps: List[WorkflowStep] = []
        raw_steps = data.get("steps", [])
        if isinstance(raw_steps, list):
            for s in raw_steps:
                if isinstance(s, dict) and "id" in s and "skill_id" in s:
                    steps.append(
                        WorkflowStep(
                            id=s["id"],
                            skill_id=s["skill_id"],
                            input_mapping=s.get("input_mapping", {}),
                        )
                    )

        workflows.append(
            WorkflowDefinition(
                id=data.get("id", wf_id),
                name=data.get("name", wf_id),
                description=data.get("description", ""),
                steps=steps,
                pack_id=pack_id,
            )
        )

    return workflows
