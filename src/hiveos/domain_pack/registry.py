"""Domain Pack registry — persists installed packs to SQLite via StorageEngine.

Namespace: ``domain_packs``
Keys: ``packs`` → {pack_id: metadata_dict}
"""

from __future__ import annotations

from typing import Dict, List, Optional

from hiveos.storage import StorageEngine

from .models import DomainPackMetadata

_NS = "domain_packs"
_K_PACKS = "packs"


class DomainPackRegistry:
    """SQLite-backed registry of installed domain packs."""

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def register(self, meta: DomainPackMetadata) -> None:
        """Add or update a pack in the registry."""
        packs = self._load()
        packs[meta.id] = {
            "id": meta.id,
            "version": meta.version,
            "name": meta.name,
            "description": meta.description,
            "min_core_version": meta.min_core_version,
            "author_name": meta.author.name,
            "author_url": meta.author.url,
            "install_path": meta.install_path,
            "installed_at": meta.installed_at,
            "enabled": meta.enabled,
            "skill_ids": [s.id for s in meta.skills],
            "workflow_ids": [w.id for w in meta.workflows],
        }
        self._save(packs)

    def unregister(self, pack_id: str) -> bool:
        """Remove a pack from the registry. Returns True if it existed."""
        packs = self._load()
        if pack_id in packs:
            del packs[pack_id]
            self._save(packs)
            return True
        return False

    def get(self, pack_id: str) -> Optional[dict]:
        """Get registry entry for a pack."""
        packs = self._load()
        return packs.get(pack_id)

    def list_all(self) -> List[dict]:
        """List all registered packs."""
        packs = self._load()
        return list(packs.values())

    def set_enabled(self, pack_id: str, enabled: bool) -> bool:
        """Enable or disable a pack. Returns True if found."""
        packs = self._load()
        if pack_id not in packs:
            return False
        packs[pack_id]["enabled"] = enabled
        self._save(packs)
        return True

    def is_installed(self, pack_id: str) -> bool:
        """Check if a pack is registered."""
        packs = self._load()
        return pack_id in packs

    def is_enabled(self, pack_id: str) -> bool:
        """Check if a pack is registered and enabled."""
        packs = self._load()
        entry = packs.get(pack_id)
        return entry is not None and entry.get("enabled", True)

    # ── Internal ──

    def _load(self) -> Dict[str, dict]:
        try:
            data = self.storage.load(_NS, _K_PACKS)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self, packs: Dict[str, dict]) -> None:
        self.storage.upsert(_NS, _K_PACKS, packs)
