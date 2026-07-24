"""Domain Pack Downloader — download and install packs from remote registry.

Orchestrates: fetch catalog → select pack → download archive → extract →
validate → install via DomainPackManager.
"""

from __future__ import annotations

import hashlib
import io
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .manager import DomainPackManager, DomainPackError
from .models import DomainPackMetadata
from .registry_client import (
    PackListing,
    RegistryClient,
    RegistryClientError,
    SearchResults,
)


class DownloadError(Exception):
    """Raised when a download/install operation fails."""


@dataclass
class DownloadProgress:
    """Progress callback data."""

    pack_id: str
    phase: str  # "search", "download", "extract", "validate", "install", "done", "error"
    message: str = ""
    percent: float = 0.0


@dataclass
class InstallResult:
    """Result of a download-and-install operation."""

    success: bool
    pack_id: str = ""
    version: str = ""
    metadata: Optional[DomainPackMetadata] = None
    error: str = ""
    phases: List[str] = field(default_factory=list)


class DomainPackDownloader:
    """High-level download and install of Domain Packs from a remote registry.

    Parameters
    ----------
    pack_manager:
        DomainPackManager for installation.
    registry_url:
        Remote registry base URL.
    api_key:
        Optional API key for authenticated registry access.
    cache_dir:
        Directory for downloaded archives and catalog cache.
    """

    def __init__(
        self,
        pack_manager: Optional[DomainPackManager] = None,
        registry_url: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        self._manager = pack_manager or DomainPackManager()
        self._cache_dir = cache_dir or Path.home() / ".hiveos" / "cache" / "domain_packs"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._client = RegistryClient(
            base_url=registry_url,
            api_key=api_key,
            cache_dir=self._cache_dir,
        )

    @property
    def client(self) -> RegistryClient:
        """Access the underlying registry client."""
        return self._client

    @property
    def manager(self) -> DomainPackManager:
        """Access the underlying pack manager."""
        return self._manager

    # ── Public API ─────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        tag: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResults:
        """Search the remote registry for Domain Packs.

        Parameters
        ----------
        query:
            Search query.
        tag:
            Optional tag filter.
        """
        try:
            if tag:
                return self._client.list_packs(tag=tag, page=page, per_page=per_page)
            return self._client.search(query, page=page, per_page=per_page)
        except RegistryClientError as exc:
            raise DownloadError(f"Registry search failed: {exc}")

    def get_available(self, tag: Optional[str] = None) -> List[PackListing]:
        """List all available packs from the registry."""
        try:
            results = self._client.list_packs(tag=tag)
            return results.packs
        except RegistryClientError as exc:
            raise DownloadError(f"Failed to list packs: {exc}")

    def get_pack_info(self, pack_id: str) -> Optional[PackListing]:
        """Get detailed info for a specific pack."""
        try:
            return self._client.get_pack(pack_id)
        except RegistryClientError as exc:
            raise DownloadError(f"Failed to get pack info: {exc}")

    def download(
        self,
        pack_id: str,
        version: Optional[str] = None,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """Download a Domain Pack archive from the registry.

        Returns path to the downloaded .tar.gz file.

        Parameters
        ----------
        pack_id:
            Pack to download.
        version:
            Specific version. None = latest.
        on_progress:
            Optional progress callback.
        """
        self._emit(on_progress, pack_id, "download", "Fetching pack metadata...")

        # Get listing for SHA256 verification
        listing = self._client.get_pack(pack_id)
        expected_sha256 = None
        if listing and listing.sha256:
            expected_sha256 = listing.sha256
            if version and listing.version != version:
                # Need version-specific info
                versions = self._client.get_versions(pack_id)
                for v in versions:
                    if v.version == version:
                        expected_sha256 = v.sha256 or None
                        break

        self._emit(on_progress, pack_id, "download", f"Downloading {pack_id}...")
        try:
            archive_path = self._client.download_pack(
                pack_id,
                version=version,
                expected_sha256=expected_sha256,
            )
        except RegistryClientError as exc:
            self._emit(on_progress, pack_id, "error", str(exc))
            raise DownloadError(f"Download failed: {exc}")

        self._emit(on_progress, pack_id, "download", f"Downloaded to {archive_path}")
        return archive_path

    def download_and_install(
        self,
        pack_id: str,
        version: Optional[str] = None,
        core_version: str = "1.0.0",
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> InstallResult:
        """Download a pack from the registry and install it.

        Full pipeline: download → extract → validate → install.

        Parameters
        ----------
        pack_id:
            Pack identifier.
        version:
            Specific version. None = latest.
        core_version:
            Current HiveOS core version for compatibility check.
        on_progress:
            Progress callback.
        """
        phases: List[str] = []

        # Phase 1: Download
        self._emit(on_progress, pack_id, "download", "Starting download...")
        try:
            archive_path = self.download(
                pack_id, version=version, on_progress=on_progress
            )
            phases.append("download")
        except DownloadError as exc:
            return InstallResult(success=False, pack_id=pack_id, error=str(exc), phases=phases)

        # Phase 2: Extract
        self._emit(on_progress, pack_id, "extract", "Extracting archive...")
        try:
            extract_dir = self._extract_archive(archive_path, pack_id)
            phases.append("extract")
        except Exception as exc:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                error=f"Extraction failed: {exc}",
                phases=phases,
            )

        # Phase 3: Find pack root (handle single-dir wrapper)
        pack_root = self._find_pack_root(extract_dir)
        if pack_root is None:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                error="Archive does not contain a valid Domain Pack (no domain.yaml found)",
                phases=phases,
            )

        # Phase 4: Validate + Install
        self._emit(on_progress, pack_id, "validate", "Validating pack structure...")
        phases.append("validate")

        self._emit(on_progress, pack_id, "install", "Installing...")
        try:
            metadata = self._manager.pack_manager_install(pack_root, core_version=core_version)
            phases.append("install")
        except DomainPackError as exc:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                error=f"Install failed: {exc}",
                phases=phases,
            )

        self._emit(on_progress, pack_id, "done", f"Installed {metadata.name} v{metadata.version}")
        return InstallResult(
            success=True,
            pack_id=metadata.id,
            version=metadata.version,
            metadata=metadata,
            phases=phases,
        )

    def update_pack(
        self,
        pack_id: str,
        core_version: str = "1.0.0",
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> InstallResult:
        """Update an installed pack to the latest version from the registry.

        Downloads latest, compares version, and updates if newer.
        """
        self._emit(on_progress, pack_id, "download", "Checking for updates...")

        # Get current version
        try:
            current = self._manager.get_pack_sync(pack_id)
            current_version = current.version
        except DomainPackError as exc:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                error=f"Pack not installed: {exc}",
            )

        # Get latest from registry
        listing = self._client.get_pack(pack_id)
        if not listing:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                error=f"Pack '{pack_id}' not found in registry",
            )

        if listing.version == current_version:
            self._emit(on_progress, pack_id, "done", f"Already up to date ({current_version})")
            return InstallResult(
                success=True,
                pack_id=pack_id,
                version=current_version,
                phases=["check"],
            )

        # Download + install new version
        self._emit(
            on_progress,
            pack_id,
            "download",
            f"Updating {current_version} → {listing.version}...",
        )
        return self.download_and_install(
            pack_id,
            version=listing.version,
            core_version=core_version,
            on_progress=on_progress,
        )

    def get_installed_info(self) -> List[Dict]:
        """Get info about installed packs with remote version comparison."""
        installed = []
        packs = self._manager.list_installed_sync()
        for meta in packs:
            info = {
                "id": meta.id,
                "name": meta.name,
                "version": meta.version,
                "enabled": meta.enabled,
                "skills": len(meta.skills),
                "workflows": len(meta.workflows),
                "update_available": False,
                "latest_version": None,
            }

            # Check remote for updates
            try:
                listing = self._client.get_pack(meta.id)
                if listing and listing.version != meta.version:
                    info["update_available"] = True
                    info["latest_version"] = listing.version
            except Exception:
                pass  # Network failure = no update info

            installed.append(info)
        return installed

    # ── Helpers ────────────────────────────────────────────────────────

    def _extract_archive(self, archive_path: Path, pack_id: str) -> Path:
        """Extract a .tar.gz archive to a temp directory.

        Handles security: blocks path traversal (../) and absolute paths.
        """
        extract_dir = self._cache_dir / "extracted" / pack_id
        if extract_dir.exists():
            import shutil
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Security: check for path traversal
                for member in tar.getmembers():
                    member_name = member.name
                    # Block absolute paths (POSIX and Windows-style)
                    if member_name.startswith("/") or (
                        len(member_name) >= 2
                        and member_name[1] == ":"
                        and member_name[2] in ("/", "\\")
                    ):
                        raise DownloadError(
                            f"Archive contains absolute path: {member_name}"
                        )
                    # Block path traversal
                    parts = Path(member_name).parts
                    if ".." in parts:
                        raise DownloadError(
                            f"Archive contains path traversal: {member_name}"
                        )

                tar.extractall(path=extract_dir)
        except tarfile.TarError as exc:
            raise DownloadError(f"Invalid tar archive: {exc}")

        return extract_dir

    def _find_pack_root(self, directory: Path) -> Optional[Path]:
        """Find the Domain Pack root within an extracted directory.

        Handles two cases:
        1. Single subdirectory containing domain.yaml
        2. domain.yaml directly in the directory
        """
        # Case 1: domain.yaml at root
        if (directory / "domain.yaml").exists():
            return directory

        # Case 2: single subdirectory with domain.yaml
        subdirs = [d for d in directory.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            if (subdirs[0] / "domain.yaml").exists():
                return subdirs[0]

        # Case 3: search all subdirectories
        for d in directory.rglob("*"):
            if d.is_dir() and (d / "domain.yaml").exists():
                return d

        return None

    def _emit(
        self,
        callback: Optional[Callable[[DownloadProgress], None]],
        pack_id: str,
        phase: str,
        message: str,
    ) -> None:
        """Emit a progress event if callback is set."""
        if callback:
            callback(DownloadProgress(pack_id=pack_id, phase=phase, message=message))
