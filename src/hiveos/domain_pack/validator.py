"""Domain Pack validator.

Validates pack structure and content against the V1 spec.
Returns a list of error strings — empty means valid.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import yaml

# Regex for pack/skill IDs — lowercase alphanumeric + hyphens
_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Semver regex
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Executable extensions blocked in packs
_EXECUTABLE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".sh", ".bash", ".bat", ".cmd", ".ps1",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".com", ".msi",
    ".jar", ".war", ".class", ".rb", ".pl", ".php",
})

# Required manifest fields
_MANIFEST_REQUIRED = {"id", "version", "name", "description", "min_core_version", "skills"}

# Required skill fields
_SKILL_REQUIRED = {"id", "name", "version", "input_schema", "output_schema", "instruction"}


def validate_pack(pack_path: Path, core_version: str = "1.0.0") -> List[str]:
    """Validate a domain pack directory. Returns list of error messages."""
    errors: List[str] = []

    if not pack_path.is_dir():
        errors.append(f"Path is not a directory: {pack_path}")
        return errors

    # ── 1. domain.yaml must exist and parse ──
    manifest_path = pack_path / "domain.yaml"
    if not manifest_path.exists():
        errors.append("Missing required file: domain.yaml")
        return errors  # Can't continue without manifest

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in domain.yaml: {exc}")
        return errors

    if not isinstance(manifest, dict):
        errors.append("domain.yaml must contain a mapping (dict)")
        return errors

    # ── 2. Required manifest fields ──
    for field_name in _MANIFEST_REQUIRED:
        if field_name not in manifest:
            errors.append(f"domain.yaml missing required field: {field_name}")

    if not manifest.get("skills"):
        # skills list can be empty but must be present and be a list
        pass  # already caught above if missing entirely

    # ── 3. ID format ──
    pack_id = manifest.get("id", "")
    if pack_id and not _ID_RE.match(pack_id):
        errors.append(f"Pack ID must be lowercase alphanumeric with hyphens, got: '{pack_id}'")

    # ── 4. Version format ──
    version = manifest.get("version", "")
    if version and not _SEMVER_RE.match(version):
        errors.append(f"Version must be valid semver (MAJOR.MINOR.PATCH), got: '{version}'")

    # ── 5. min_core_version compatibility ──
    min_core = manifest.get("min_core_version", "")
    if min_core:
        if not _SEMVER_RE.match(min_core):
            errors.append(f"min_core_version must be valid semver, got: '{min_core}'")
        else:
            if not _version_lte(min_core, core_version):
                errors.append(
                    f"Pack requires core >= {min_core}, but current core is {core_version}"
                )

    # ── 6. Knowledge directory must exist with >= 1 file ──
    knowledge_dir = pack_path / "knowledge"
    if not knowledge_dir.exists():
        errors.append("Missing required directory: knowledge/")
    else:
        knowledge_files = [f for f in knowledge_dir.iterdir() if f.is_file()]
        if not knowledge_files:
            errors.append("knowledge/ directory is empty — must contain at least 1 file")
        # Check for executable files in knowledge/
        errors.extend(_check_executables(knowledge_dir, "knowledge/"))

    # ── 7. Skills directory ──
    skills_dir = pack_path / "skills"
    if not skills_dir.exists():
        errors.append("Missing required directory: skills/")
    else:
        # Check each skill referenced in manifest exists and is valid
        manifest_skills = manifest.get("skills", [])
        if not isinstance(manifest_skills, list):
            errors.append("manifest 'skills' must be a list")
        else:
            for skill_ref in manifest_skills:
                skill_id = skill_ref.get("id", "") if isinstance(skill_ref, dict) else str(skill_ref)
                if not skill_id:
                    errors.append("Skill entry in manifest has no 'id'")
                    continue

                skill_path = skills_dir / f"{skill_id}.yaml"
                if not skill_path.exists():
                    # Also try .yml
                    skill_path = skills_dir / f"{skill_id}.yml"
                    if not skill_path.exists():
                        errors.append(f"Referenced skill file not found: skills/{skill_id}.yaml")
                        continue

                # Validate skill YAML
                skill_errors = _validate_skill_file(skill_path)
                errors.extend(skill_errors)

        # Check for executable files in skills/
        errors.extend(_check_executables(skills_dir, "skills/"))

    # ── 8. Workflows directory (optional) ──
    workflows_dir = pack_path / "workflows"
    if workflows_dir.exists():
        manifest_workflows = manifest.get("workflows", [])
        if isinstance(manifest_workflows, list):
            for wf_ref in manifest_workflows:
                wf_id = wf_ref.get("id", "") if isinstance(wf_ref, dict) else str(wf_ref)
                if not wf_id:
                    errors.append("Workflow entry in manifest has no 'id'")
                    continue

                wf_path = workflows_dir / f"{wf_id}.yaml"
                if not wf_path.exists():
                    wf_path = workflows_dir / f"{wf_id}.yml"
                    if not wf_path.exists():
                        errors.append(f"Referenced workflow file not found: workflows/{wf_id}.yaml")
                        continue

                wf_errors = _validate_workflow_file(wf_path)
                errors.extend(wf_errors)

        errors.extend(_check_executables(workflows_dir, "workflows/"))

    # ── 9. No executable files anywhere in pack ──
    errors.extend(_check_executables(pack_path, "pack root", recursive=True, exclude={"knowledge", "skills", "workflows"}))

    return errors


def validate_pack_dry_run(pack_path: Path, core_version: str = "1.0.0") -> tuple[bool, List[str]]:
    """Validate a pack without installing. Returns (is_valid, errors)."""
    errors = validate_pack(pack_path, core_version=core_version)
    return (len(errors) == 0, errors)


# ── Internal helpers ────────────────────────────────────────────────────────


def _validate_skill_file(path: Path) -> List[str]:
    """Validate a single skill YAML file."""
    errors: List[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in {path.name}: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{path.name} must contain a mapping")
        return errors

    for field_name in _SKILL_REQUIRED:
        if field_name not in data:
            errors.append(f"Skill {path.name} missing required field: {field_name}")

    # Validate ID format
    skill_id = data.get("id", "")
    if skill_id and not _ID_RE.match(skill_id):
        errors.append(f"Skill ID must be lowercase alphanumeric with hyphens, got: '{skill_id}'")

    # Validate version
    skill_version = data.get("version", "")
    if skill_version and not _SEMVER_RE.match(skill_version):
        errors.append(f"Skill version must be valid semver, got: '{skill_version}'")

    return errors


def _validate_workflow_file(path: Path) -> List[str]:
    """Validate a single workflow YAML file."""
    errors: List[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in {path.name}: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{path.name} must contain a mapping")
        return errors

    if "id" not in data:
        errors.append(f"Workflow {path.name} missing required field: id")

    steps = data.get("steps", [])
    if not isinstance(steps, list):
        errors.append(f"Workflow {path.name} 'steps' must be a list")
    else:
        for step in steps:
            if not isinstance(step, dict):
                errors.append(f"Workflow step must be a mapping")
                continue
            if "id" not in step:
                errors.append(f"Workflow step missing 'id'")
            if "skill_id" not in step:
                errors.append(f"Workflow step '{step.get('id', '?')}' missing 'skill_id'")

    return errors


def _check_executables(
    directory: Path,
    label: str,
    recursive: bool = False,
    exclude: set[str] | None = None,
) -> List[str]:
    """Check for executable files in a directory."""
    errors: List[str] = []
    exclude = exclude or set()

    if recursive:
        for item in directory.rglob("*"):
            if not item.is_file():
                continue
            # Skip excluded subdirectories
            rel = item.relative_to(directory)
            if any(rel.parts[0] == ex for ex in exclude if rel.parts):
                continue
            if item.suffix.lower() in _EXECUTABLE_EXTENSIONS:
                errors.append(
                    f"Executable code file found in {label}: {item.relative_to(directory)}"
                )
    else:
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in _EXECUTABLE_EXTENSIONS:
                errors.append(f"Executable code file found in {label}: {item.name}")

    return errors


def _version_lte(v1: str, v2: str) -> bool:
    """Check if v1 <= v2 in semver order."""
    try:
        parts1 = tuple(int(x) for x in v1.split("."))
        parts2 = tuple(int(x) for x in v2.split("."))
        return parts1 <= parts2
    except (ValueError, AttributeError):
        return False
