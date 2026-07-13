"""HiveOS Package Registry — discover, publish, and manage packages.

The registry is a YAML-based catalog of packages that can be:
- Published locally or to a remote registry URL
- Searched by name, tag, or keyword
- Discovered by other HiveOS nodes
"""

from .registry import PackageRegistry, RegistryEntry, RegistryConfig
from .remote import RemoteRegistryClient

__all__ = ["PackageRegistry", "RegistryEntry", "RegistryConfig", "RemoteRegistryClient"]
