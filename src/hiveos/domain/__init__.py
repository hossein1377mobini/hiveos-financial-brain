"""HiveOS Domain Plugin — pluggable knowledge domains for agent teams.

The Domain Registry extends the basic DomainManager with StorageEngine-backed
persistence, dependency resolution, learning, and suggestion capabilities.
"""

from .manager import DomainInfo, DomainManager
from .registry import DomainRegistry, export_domain, import_domain

__all__ = [
    "DomainInfo",
    "DomainManager",
    "DomainRegistry",
    "export_domain",
    "import_domain",
]
