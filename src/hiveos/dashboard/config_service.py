"""YAML-backed configuration service for HiveOS V2."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

DEFAULT_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "127.0.0.1",
        "port": 8420,
    },
    "ai": {
        "provider": "local",
        "model": "llama3.1",
        "api_url": "http://localhost:11434",
    },
    "storage": {
        "data_dir": "~/.hiveos/data",
        "db_path": "~/.hiveos/data/hiveos.db",
    },
    "logging": {
        "level": "INFO",
    },
}


class ConfigService:
    """YAML-based config with dot-notation get/set.

    Auto-creates default config if file missing.
    Writes back on every ``set()``.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".hiveos" / "config.yaml"
        self._config: Dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value by dot-separated key (e.g. ``server.port``)."""
        parts = key.split(".")
        value = self._config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a value by dot-separated key and persist to disk."""
        parts = key.split(".")
        target = self._config
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
        self._save()

    def reload(self) -> None:
        """Re-read config from disk, discarding in-memory changes."""
        self._config.clear()
        self._load()

    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the full config dict."""
        return copy.deepcopy(self._config)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
            self._config = parsed if isinstance(parsed, dict) else {}
        else:
            self._config = copy.deepcopy(DEFAULT_CONFIG)
            self._save()

    def _save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
