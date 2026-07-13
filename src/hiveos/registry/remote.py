"""
Remote Registry Client — push/pull packages to/from remote registry servers.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import urllib.request
import urllib.error
from datetime import datetime

from .registry import RegistryEntry, PackageRegistry


class RemoteRegistryClient:
    """Client for communicating with remote HiveOS package registries."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HiveOS/0.1.0",
        }
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(self, endpoint: str, method: str = "GET",
                  data: Optional[dict] = None, timeout: int = 30) -> Optional[dict]:
        url = f"{self.base_url}/api/v1/registry/{endpoint.lstrip('/')}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            msg = ""
            try:
                msg = e.read().decode("utf-8")[:200]
            except Exception:
                pass
            raise ConnectionError(f"HTTP {e.code} from {url}: {msg}") from e
        except Exception as e:
            raise ConnectionError(f"Failed to reach {url}: {e}") from e

    def publish(self, entry: RegistryEntry) -> bool:
        """Publish a package to the remote registry."""
        result = self._request("publish", method="POST", data=entry.to_dict())
        return result is not None and result.get("success", False)

    def search(self, query: str) -> List[RegistryEntry]:
        """Search packages on the remote registry."""
        result = self._request(f"search?q={urllib.parse.quote(query)}")
        if result and "results" in result:
            return [RegistryEntry.from_dict(r) for r in result["results"]]
        return []

    def list_packages(self, tag: Optional[str] = None) -> List[RegistryEntry]:
        """List packages from the remote registry."""
        endpoint = f"list"
        if tag:
            endpoint += f"?tag={urllib.parse.quote(tag)}"
        result = self._request(endpoint)
        if result and "packages" in result:
            return [RegistryEntry.from_dict(r) for r in result["packages"]]
        return []

    def info(self, name: str, version: Optional[str] = None) -> Optional[RegistryEntry]:
        """Get package info from the remote registry."""
        endpoint = f"info/{urllib.parse.quote(name)}"
        if version:
            endpoint += f"/{urllib.parse.quote(version)}"
        result = self._request(endpoint)
        if result and "package" in result:
            return RegistryEntry.from_dict(result["package"])
        return None

    def pull_and_merge(self, local_registry: PackageRegistry,
                       tag: Optional[str] = None) -> int:
        """Pull remote packages and merge into the local registry.

        Returns the number of new/updated packages.
        """
        remote_packages = self.list_packages(tag=tag)
        count = 0
        for entry in remote_packages:
            local = local_registry.get(entry.name, entry.version)
            if local is None:
                local_registry.publish(entry)
                count += 1
            else:
                # Update metadata only
                entry.published_at = local.published_at
                local_registry.publish(entry, overwrite=True)
                count += 1
        return count
