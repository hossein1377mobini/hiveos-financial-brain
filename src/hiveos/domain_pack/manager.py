"""Domain Pack Manager — lifecycle operations for Domain Packs.

Install, remove, enable, disable, update, query.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from hiveos.storage import StorageEngine

from .loader import load_pack
from .models import DomainPackMetadata, SkillDefinition, WorkflowDefinition
from .registry import DomainPackRegistry
from .validator import validate_pack


class DomainPackError(Exception):
    """Raised when a domain pack operation fails."""


class DomainPackManager:
    """Manages the lifecycle of Domain Packs.

    Parameters
    ----------
    base_dir:
        Root directory where packs are stored (default: ``~/.hiveos/domains/``).
    storage:
        StorageEngine instance for persistence.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        storage: Optional[StorageEngine] = None,
    ):
        self.base_dir = Path(base_dir or Path.home() / ".hiveos" / "domains")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._storage = storage or StorageEngine()
        self._registry = DomainPackRegistry(self._storage)

    # ── Install ─────────────────────────────────────────────────────────

    async def install(self, pack_source: Path, core_version: str = "1.0.0") -> DomainPackMetadata:
        """Install a Domain Pack from *pack_source* directory.

        1. Validate structure.
        2. Copy to base_dir/<pack_id>/.
        3. Load into models.
        4. Register in registry.
        5. Return metadata.
        """
        pack_source = Path(pack_source).resolve()
        if not pack_source.is_dir():
            raise DomainPackError(f"Source is not a directory: {pack_source}")

        # Validate
        errors = validate_pack(pack_source, core_version=core_version)
        if errors:
            raise DomainPackError(
                "Pack validation failed:\n  " + "\n  ".join(errors)
            )

        # Load to get the pack_id
        temp_meta = load_pack(pack_source)

        # Check not already installed
        if self._registry.is_installed(temp_meta.id):
            raise DomainPackError(
                f"Pack '{temp_meta.id}' is already installed. "
                "Remove it first or use update."
            )

        # Copy into base_dir
        target = self.base_dir / temp_meta.id
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(pack_source, target)

        # Load from installed location
        meta = load_pack(target)
        meta.installed_at = datetime.now(timezone.utc).isoformat()
        meta.enabled = True

        # Register
        self._registry.register(meta)

        return meta

    # ── Remove ──────────────────────────────────────────────────────────

    async def remove(self, pack_id: str) -> bool:
        """Remove an installed Domain Pack.

        Deletes directory and registry entry. Returns True on success.
        """
        entry = self._registry.get(pack_id)
        if not entry:
            raise DomainPackError(f"Pack '{pack_id}' is not installed")

        # Delete directory
        install_path = Path(entry.get("install_path", ""))
        if install_path.exists():
            shutil.rmtree(install_path)

        # Unregister
        self._registry.unregister(pack_id)
        return True

    # ── Enable / Disable ────────────────────────────────────────────────

    async def enable(self, pack_id: str) -> bool:
        """Enable a disabled Domain Pack."""
        if not self._registry.is_installed(pack_id):
            raise DomainPackError(f"Pack '{pack_id}' is not installed")
        return self._registry.set_enabled(pack_id, True)

    async def disable(self, pack_id: str) -> bool:
        """Disable a Domain Pack (content becomes unavailable)."""
        if not self._registry.is_installed(pack_id):
            raise DomainPackError(f"Pack '{pack_id}' is not installed")
        return self._registry.set_enabled(pack_id, False)

    # ── Query ───────────────────────────────────────────────────────────

    async def list_installed(self) -> List[DomainPackMetadata]:
        """List all installed Domain Packs."""
        entries = self._registry.list_all()
        result: List[DomainPackMetadata] = []
        for entry in entries:
            install_path = Path(entry.get("install_path", ""))
            if install_path.exists():
                try:
                    meta = load_pack(install_path)
                    meta.enabled = entry.get("enabled", True)
                    meta.installed_at = entry.get("installed_at", "")
                    result.append(meta)
                except Exception:
                    pass
        return result

    async def get_pack(self, pack_id: str) -> DomainPackMetadata:
        """Get metadata for a specific installed pack."""
        entry = self._registry.get(pack_id)
        if not entry:
            raise DomainPackError(f"Pack '{pack_id}' is not installed")

        install_path = Path(entry["install_path"])
        if not install_path.exists():
            raise DomainPackError(
                f"Pack '{pack_id}' directory missing at {install_path}"
            )

        meta = load_pack(install_path)
        meta.enabled = entry.get("enabled", True)
        meta.installed_at = entry.get("installed_at", "")
        return meta

    async def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Find a Skill by ID across all installed packs."""
        packs = await self.list_installed()
        for pack in packs:
            if not pack.enabled:
                continue
            for skill in pack.skills:
                if skill.id == skill_id:
                    return skill
        return None

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Find a Workflow by ID across all installed packs."""
        packs = await self.list_installed()
        for pack in packs:
            if not pack.enabled:
                continue
            for wf in pack.workflows:
                if wf.id == workflow_id:
                    return wf
        return None

    async def list_skills(self, pack_id: Optional[str] = None) -> List[SkillDefinition]:
        """List Skills, optionally filtered to a single pack."""
        skills: List[SkillDefinition] = []
        packs = await self.list_installed()
        for pack in packs:
            if not pack.enabled:
                continue
            if pack_id and pack.id != pack_id:
                continue
            skills.extend(pack.skills)
        return skills

    async def list_workflows(
        self, pack_id: Optional[str] = None
    ) -> List[WorkflowDefinition]:
        """List Workflows, optionally filtered to a single pack."""
        workflows: List[WorkflowDefinition] = []
        packs = await self.list_installed()
        for pack in packs:
            if not pack.enabled:
                continue
            if pack_id and pack.id != pack_id:
                continue
            workflows.extend(pack.workflows)
        return workflows

    # ── Update ──────────────────────────────────────────────────────────

    async def update(
        self, pack_id: str, new_pack_source: Path, core_version: str = "1.0.0"
    ) -> DomainPackMetadata:
        """Update an installed Domain Pack to a new version.

        1. Validate the new pack.
        2. Remove old version.
        3. Install new version.
        """
        entry = self._registry.get(pack_id)
        if not entry:
            raise DomainPackError(f"Pack '{pack_id}' is not installed — use install instead")

        # Validate new pack
        new_pack_source = Path(new_pack_source).resolve()
        errors = validate_pack(new_pack_source, core_version=core_version)
        if errors:
            raise DomainPackError(
                "New pack validation failed:\n  " + "\n  ".join(errors)
            )

        new_meta = load_pack(new_pack_source)
        if new_meta.id != pack_id:
            raise DomainPackError(
                f"New pack ID '{new_meta.id}' does not match installed pack ID '{pack_id}'"
            )

        # Remove old
        old_path = Path(entry.get("install_path", ""))
        if old_path.exists():
            shutil.rmtree(old_path)
        self._registry.unregister(pack_id)

        # Install new
        target = self.base_dir / pack_id
        shutil.copytree(new_pack_source, target)

        meta = load_pack(target)
        meta.installed_at = datetime.now(timezone.utc).isoformat()
        meta.enabled = entry.get("enabled", True)

        self._registry.register(meta)
        return meta

    # ── Sync wrappers (for non-async callers like CLI/Downloader) ───────

    def install_sync(self, pack_source: Path, core_version: str = "1.0.0") -> DomainPackMetadata:
        """Synchronous wrapper for install()."""
        import asyncio
        return asyncio.run(self.install(pack_source, core_version=core_version))

    def pack_manager_install(
        self, pack_source: Path, core_version: str = "1.0.0"
    ) -> DomainPackMetadata:
        """Synchronous install (alias for install_sync, used by downloader)."""
        return self.install_sync(pack_source, core_version=core_version)

    def remove_sync(self, pack_id: str) -> bool:
        """Synchronous wrapper for remove()."""
        import asyncio
        return asyncio.run(self.remove(pack_id))

    def enable_sync(self, pack_id: str) -> bool:
        """Synchronous wrapper for enable()."""
        import asyncio
        return asyncio.run(self.enable(pack_id))

    def disable_sync(self, pack_id: str) -> bool:
        """Synchronous wrapper for disable()."""
        import asyncio
        return asyncio.run(self.disable(pack_id))

    def list_installed_sync(self) -> List[DomainPackMetadata]:
        """Synchronous wrapper for list_installed()."""
        import asyncio
        return asyncio.run(self.list_installed())

    def get_pack_sync(self, pack_id: str) -> DomainPackMetadata:
        """Synchronous wrapper for get_pack()."""
        import asyncio
        return asyncio.run(self.get_pack(pack_id))

    def update_sync(
        self, pack_id: str, new_pack_source: Path, core_version: str = "1.0.0"
    ) -> DomainPackMetadata:
        """Synchronous wrapper for update()."""
        import asyncio
        return asyncio.run(self.update(pack_id, new_pack_source, core_version=core_version))
