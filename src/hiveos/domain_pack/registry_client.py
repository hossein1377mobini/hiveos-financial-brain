"""Remote Domain Pack Registry Client.

Communicates with a remote HTTP(S) registry to list, search, and download
Domain Packs. Supports configurable base URL, API key auth, and caching.

Privacy: All requests check against PrivacyConfig before sending (ADR-0017).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hiveos.privacy import DataClassification, NetworkGuard, PrivacyConfig, PrivacyViolation


# ── Default registry URL ───────────────────────────────────────────────
DEFAULT_REGISTRY_URL = "https://registry.hiveos.dev/api/v1"
DEFAULT_CACHE_TTL = 3600  # 1 hour


class RegistryClientError(Exception):
    """Raised when a registry operation fails."""


@dataclass
class PackListing:
    """A pack entry as returned by the remote registry."""

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    downloads: int = 0
    size_bytes: int = 0
    download_url: str = ""
    sha256: str = ""
    min_core_version: str = "1.0.0"
    published_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "downloads": self.downloads,
            "size_bytes": self.size_bytes,
            "download_url": self.download_url,
            "sha256": self.sha256,
            "min_core_version": self.min_core_version,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SearchResults:
    """Search results from the registry."""

    query: str
    total: int
    packs: List[PackListing] = field(default_factory=list)


class RegistryClient:
    """HTTP client for the HiveOS Domain Pack Registry.

    Parameters
    ----------
    base_url:
        Registry API base URL.
    api_key:
        Optional API key for authenticated requests.
    cache_dir:
        Directory for caching catalog responses.
    cache_ttl:
        Cache time-to-live in seconds.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        timeout: int = 30,
        privacy_config: Optional[PrivacyConfig] = None,
    ):
        self.base_url = (base_url or DEFAULT_REGISTRY_URL).rstrip("/")
        self.api_key = api_key
        self.cache_dir = cache_dir or Path.home() / ".hiveos" / "cache" / "registry"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        
        # Privacy guard (ADR-0017)
        self.privacy_config = privacy_config
        self._privacy_guard = NetworkGuard(privacy_config) if privacy_config else None
    
    def _check_privacy(self, url: str) -> None:
        """Check if request is allowed by privacy policy."""
        if self._privacy_guard:
            result = self._privacy_guard.check_egress(
                url=url,
                data_types=[DataClassification.METADATA],
                endpoint_id="registry",
            )
            if not result.allowed:
                raise PrivacyViolation(
                    f"Registry request blocked: {result.reason}\n"
                    f"URL: {url}\n"
                    f"To enable: hive privacy enable registry"
                )

    # ── Public API ─────────────────────────────────────────────────────

    def list_packs(
        self,
        tag: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        use_cache: bool = True,
    ) -> SearchResults:
        """List available packs from the registry.

        Parameters
        ----------
        tag:
            Optional tag filter.
        page:
            Page number (1-indexed).
        per_page:
            Results per page.
        use_cache:
            Use local cache if available.
        """
        params: Dict[str, str] = {
            "page": str(page),
            "per_page": str(per_page),
        }
        if tag:
            params["tag"] = tag

        data = self._get("/packs", params=params, use_cache=use_cache)
        return self._parse_search_results(data)

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResults:
        """Search packs by name, description, or tags.

        Parameters
        ----------
        query:
            Search query string.
        page:
            Page number (1-indexed).
        per_page:
            Results per page.
        """
        params = {
            "q": query,
            "page": str(page),
            "per_page": str(per_page),
        }
        data = self._get("/packs/search", params=params, use_cache=False)
        return self._parse_search_results(data)

    def get_pack(self, pack_id: str) -> Optional[PackListing]:
        """Get detailed info for a specific pack.

        Parameters
        ----------
        pack_id:
            The pack identifier.
        """
        try:
            data = self._get(f"/packs/{pack_id}")
            packs = self._parse_pack_list(data if isinstance(data, dict) else {"packs": [data]})
            return packs[0] if packs else None
        except RegistryClientError:
            return None

    def get_versions(self, pack_id: str) -> List[PackListing]:
        """Get all published versions of a pack."""
        data = self._get(f"/packs/{pack_id}/versions")
        items = data if isinstance(data, list) else data.get("versions", [])
        return [self._parse_pack_listing(item) for item in items]

    def download_pack(
        self,
        pack_id: str,
        version: Optional[str] = None,
        dest: Optional[Path] = None,
        expected_sha256: Optional[str] = None,
    ) -> Path:
        """Download a domain pack archive (.tar.gz).

        Parameters
        ----------
        pack_id:
            Pack identifier.
        version:
            Specific version. None = latest.
        dest:
            Destination file path. None = auto.
        expected_sha256:
            SHA256 hash to verify download integrity.

        Returns
        -------
        Path to the downloaded archive.

        Raises
        ------
        RegistryClientError
            On download failure or hash mismatch.
        """
        url = self._build_download_url(pack_id, version)

        if dest is None:
            dest = self.cache_dir / "downloads" / f"{pack_id}-{version or 'latest'}.tar.gz"
        dest.parent.mkdir(parents=True, exist_ok=True)

        self._download_file(url, dest)

        if expected_sha256:
            self._verify_sha256(dest, expected_sha256)

        return dest

    # ── Internal ───────────────────────────────────────────────────────

    def _build_download_url(self, pack_id: str, version: Optional[str]) -> str:
        """Build the download URL for a pack."""
        if version:
            return f"{self.base_url}/packs/{pack_id}/versions/{version}/download"
        return f"{self.base_url}/packs/{pack_id}/download"

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Any:
        """Make a GET request to the registry.

        Checks cache first if use_cache=True.
        """
        url = self._build_url(path, params)
        cache_key = self._cache_key(url)

        # Check cache
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached is not None:
                return cached

        # Privacy check (ADR-0017)
        self._check_privacy(url)

        # Make request
        try:
            headers = {"Accept": "application/json", "User-Agent": "HiveOS-DomainPack-Client/1.0"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            req = Request(url, headers=headers, method="GET")
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise RegistryClientError(f"Not found: {path}")
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RegistryClientError(
                f"Registry request failed ({exc.code}): {body or exc.reason}"
            )
        except URLError as exc:
            raise RegistryClientError(f"Network error: {exc.reason}")
        except json.JSONDecodeError as exc:
            raise RegistryClientError(f"Invalid JSON from registry: {exc}")

        # Cache response
        if use_cache:
            self._write_cache(cache_key, data)

        return data

    def _download_file(self, url: str, dest: Path) -> None:
        """Download a file from URL to dest with progress."""
        # Privacy check (ADR-0017)
        self._check_privacy(url)
        
        try:
            headers = {"User-Agent": "HiveOS-DomainPack-Client/1.0"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            req = Request(url, headers=headers, method="GET")
            with urlopen(req, timeout=self.timeout * 3) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(dest, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

        except HTTPError as exc:
            dest.unlink(missing_ok=True)
            raise RegistryClientError(f"Download failed ({exc.code}): {exc.reason}")
        except URLError as exc:
            dest.unlink(missing_ok=True)
            raise RegistryClientError(f"Download network error: {exc.reason}")

    def _verify_sha256(self, path: Path, expected: str) -> None:
        """Verify file SHA256 hash."""
        import hashlib

        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)

        actual = h.hexdigest()
        if actual != expected:
            path.unlink(missing_ok=True)
            raise RegistryClientError(
                f"SHA256 mismatch: expected {expected}, got {actual}"
            )

    def _build_url(self, path: str, params: Optional[Dict[str, str]] = None) -> str:
        """Build full URL with query params."""
        url = f"{self.base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query:
                url += f"?{query}"
        return url

    def _cache_key(self, url: str) -> Path:
        """Derive a cache file path from URL."""
        import hashlib

        h = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{h}.json"

    def _read_cache(self, key: Path) -> Optional[Any]:
        """Read cache if fresh enough."""
        if not key.exists():
            return None
        age = time.time() - key.stat().st_mtime
        if age > self.cache_ttl:
            return None
        try:
            return json.loads(key.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_cache(self, key: Path, data: Any) -> None:
        """Write data to cache file."""
        try:
            key.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass  # Cache write failure is non-fatal

    # ── Parsing ────────────────────────────────────────────────────────

    def _parse_search_results(self, data: Any) -> SearchResults:
        """Parse a search/list response into SearchResults."""
        if isinstance(data, list):
            return SearchResults(
                query="",
                total=len(data),
                packs=[self._parse_pack_listing(item) for item in data],
            )

        packs_raw = data.get("packs", data.get("results", data.get("data", [])))
        if isinstance(packs_raw, dict):
            packs_raw = list(packs_raw.values())

        return SearchResults(
            query=data.get("query", ""),
            total=data.get("total", len(packs_raw)),
            packs=[self._parse_pack_listing(item) for item in packs_raw],
        )

    def _parse_pack_listing(self, data: Dict[str, Any]) -> PackListing:
        """Parse a single pack entry."""
        return PackListing(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            downloads=data.get("downloads", 0),
            size_bytes=data.get("size_bytes", 0),
            download_url=data.get("download_url", ""),
            sha256=data.get("sha256", ""),
            min_core_version=data.get("min_core_version", "1.0.0"),
            published_at=data.get("published_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def _parse_pack_list(self, data: Dict[str, Any]) -> List[PackListing]:
        """Parse a response containing a list of packs."""
        packs_raw = data.get("packs", data.get("results", []))
        if isinstance(packs_raw, dict):
            packs_raw = list(packs_raw.values())
        return [self._parse_pack_listing(item) for item in packs_raw]
