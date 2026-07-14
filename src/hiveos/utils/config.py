"""
Configuration manager for HiveOS.
"""

from pathlib import Path
import yaml
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

DEFAULT_CONFIG = {
    "version": "0.9.2",
    "knowledge_dir": "docs",
    "package_dir": "~/.hiveos/packages",
    "flow_dir": "prototype",
    "engine": {
        "max_concurrent_agents": 3,
        "default_timeout_minutes": 10,
        "default_retry_count": 2,
        "trace_enabled": True,
    },
    "delivery": {
        "default_format": "markdown",
        "default_destination": "origin",
    },
    "gateway": {
        "enabled": False,
        "port": 8080,
    },
}

class ConfigManager:
    """Manages HiveOS configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".hiveos" / "config.yaml"
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            console.print(f"✅ Loaded config from: {self.config_path}")
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            console.print(f"🆕 Created default config: {self.config_path}")
        
        return self._config
    
    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dot-separated key."""
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
    
    def set(self, key: str, value: Any):
        """Set a config value by dot-separated key."""
        parts = key.split(".")
        target = self._config
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
        self.save()
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get all config as dict."""
        return self._config
