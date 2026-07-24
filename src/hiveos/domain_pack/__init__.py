"""Domain Pack Manager — install, enable, disable, remove, update Domain Packs.

V1: flat directory packs, declarative only, zero executable code.
Includes remote registry download support.
"""

from .downloader import (
    DomainPackDownloader,
    DownloadError,
    DownloadProgress,
    InstallResult,
)
from .loader import load_pack
from .manager import DomainPackError, DomainPackManager
from .models import (
    AuthorInfo,
    DomainPackMetadata,
    SkillDefinition,
    WorkflowDefinition,
    WorkflowStep,
)
from .registry_client import (
    PackListing,
    RegistryClient,
    RegistryClientError,
    SearchResults,
)
from .registry import DomainPackRegistry
from .validator import validate_pack, validate_pack_dry_run

__all__ = [
    "AuthorInfo",
    "DownloadError",
    "DownloadProgress",
    "DomainPackDownloader",
    "DomainPackError",
    "DomainPackManager",
    "DomainPackMetadata",
    "DomainPackRegistry",
    "InstallResult",
    "PackListing",
    "RegistryClient",
    "RegistryClientError",
    "SearchResults",
    "SkillDefinition",
    "WorkflowDefinition",
    "WorkflowStep",
    "load_pack",
    "validate_pack",
    "validate_pack_dry_run",
]
