"""Domain Pack data models.

Pure dataclasses — no side effects, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuthorInfo:
    """Author metadata from domain.yaml."""
    name: str = ""
    url: str = ""


@dataclass
class SkillDefinition:
    """Parsed Skill YAML — one per file in skills/."""
    id: str
    name: str
    version: str = "0.0.0"
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    knowledge_requirements: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    model: Dict[str, Any] = field(default_factory=dict)
    instruction: str = ""
    # Set by loader — which pack owns this skill
    pack_id: str = ""


@dataclass
class WorkflowStep:
    """A single step inside a WorkflowDefinition."""
    id: str
    skill_id: str
    input_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Parsed Workflow YAML — one file in workflows/."""
    id: str
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    # Set by loader — which pack owns this workflow
    pack_id: str = ""


@dataclass
class DomainPackMetadata:
    """Complete metadata for an installed Domain Pack."""
    id: str
    version: str
    name: str
    description: str
    min_core_version: str = "1.0.0"
    author: AuthorInfo = field(default_factory=AuthorInfo)
    # Skill / workflow references from manifest (populated by loader)
    skills: List[SkillDefinition] = field(default_factory=list)
    workflows: List[WorkflowDefinition] = field(default_factory=list)
    # Registry fields (set during install)
    install_path: str = ""
    installed_at: str = ""
    enabled: bool = True
