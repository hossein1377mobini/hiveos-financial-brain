"""HiveOS Mothership-Satellite sync module."""
from pathlib import Path
from .node_registry import NodeRegistry, SatelliteNode
from .sync_service import SyncService

SYNC_DIR = Path.home() / ".hiveos" / "sync"

__all__ = ["NodeRegistry", "SatelliteNode", "SyncService", "SYNC_DIR"]
