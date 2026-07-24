"""
Update checker — queries GitHub Releases for newer HiveOS versions.
Supports the CL-03 auto-update skeleton: lightweight, offline-tolerant,
HTTP-cache-friendly version comparison.

Privacy: All requests check against PrivacyConfig before sending (ADR-0017).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

from hiveos import __version__ as HIVEOS_VERSION
from hiveos.privacy import DataClassification, NetworkGuard, PrivacyConfig, PrivacyViolation

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com/repos/hossein1377mobini/hiveos-financial-brain/releases/latest"
TIMEOUT_SECONDS = 5


@dataclass
class UpdateInfo:
    """Result of an update check."""

    current_version: str
    latest_version: Optional[str] = None
    download_url: Optional[str] = None
    release_notes: Optional[str] = None
    error: Optional[str] = None

    @property
    def update_available(self) -> bool:
        if self.latest_version is None or self.error:
            return False
        try:
            return _parse_version(self.latest_version) > _parse_version(self.current_version)
        except ValueError:
            return False

    @property
    def is_current(self) -> bool:
        """True when latest_version is set, not an error, and NOT newer."""
        if self.error or self.latest_version is None:
            return False
        try:
            return _parse_version(self.latest_version) <= _parse_version(self.current_version)
        except ValueError:
            return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)\.(\d+))?$")


def _parse_version(ver: str) -> tuple:
    """Parse a semver string into a comparable tuple.

    '0.9.1' -> (0, 9, 1, 999, 0)
    '0.10.0-alpha.1' -> (0, 10, 0, 0, 1)
    """
    m = _VERSION_PATTERN.match(ver.strip())
    if not m:
        raise ValueError(f"Cannot parse version: {ver}")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre_type = m.group(4)
    pre_num = int(m.group(5)) if m.group(5) else 0
    # Pre-release weight: alpha=0, beta=1, rc=2, release=999
    weight = {"alpha": 0, "beta": 1, "rc": 2}.get(pre_type, 999)
    return (major, minor, patch, weight, pre_num)


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

class UpdateChecker:
    """Lightweight update-checker against GitHub Releases API.

    Usage::

        info = UpdateChecker().check()
        if info.update_available:
            print(f"Upgrade {info.current_version} -> {info.latest_version}")
    """

    def __init__(
        self,
        *,
        current_version: Optional[str] = None,
        api_url: str = GITHUB_API,
        timeout: int = TIMEOUT_SECONDS,
        privacy_config: Optional[PrivacyConfig] = None,
    ):
        self._current = current_version or HIVEOS_VERSION
        self._api_url = api_url
        self._timeout = timeout
        
        # Privacy guard (ADR-0017)
        self._privacy_guard = NetworkGuard(privacy_config) if privacy_config else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self) -> UpdateInfo:
        """Query GitHub for the latest release and return an UpdateInfo."""
        try:
            data = self._fetch_latest_release()
        except PrivacyViolation as exc:
            return UpdateInfo(
                current_version=self._current,
                error=f"Privacy policy violation: {exc}",
            )
        except URLError as exc:
            return UpdateInfo(
                current_version=self._current,
                error=f"Network error: {exc.reason}",
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            return UpdateInfo(
                current_version=self._current,
                error=f"API response error: {exc}",
            )

        latest_tag = data.get("tag_name", "").lstrip("v")
        download_url = data.get("html_url", "")
        body = data.get("body", "") or ""

        return UpdateInfo(
            current_version=self._current,
            latest_version=latest_tag or None,
            download_url=download_url,
            release_notes=_trim_notes(body),
            error=None,
        )

    def check_and_notify(self) -> str:
        """Convenience: run ``check()`` and return a human-readable message."""
        info = self.check()
        return self._format_message(info)

    @staticmethod
    def format(info: UpdateInfo) -> str:
        """Format an UpdateInfo into a human-readable message."""
        return UpdateChecker._format_message(info)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_latest_release(self) -> dict:
        # Privacy check (ADR-0017)
        if self._privacy_guard:
            result = self._privacy_guard.check_egress(
                url=self._api_url,
                data_types=[DataClassification.METADATA],
                endpoint_id="updates",
            )
            if not result.allowed:
                raise PrivacyViolation(
                    f"Update check blocked: {result.reason}\n"
                    f"To enable: hive privacy enable updates"
                )
        
        req = Request(
            self._api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "HiveOS/auto-update",
            },
        )
        with urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _format_message(info: UpdateInfo) -> str:
        from rich.markdown import Markdown
        from rich.console import Console
        from rich.panel import Panel
        from rich import print as rprint

        console = Console()

        if info.error:
            rprint(Panel(
                f"[yellow]⚠ Update check failed[/yellow]\n  {info.error}",
                title="HiveOS Update",
                width=60,
            ))
            return info.error

        if info.update_available:
            rprint(Panel(
                f"[bold green]🚀 New version available![/bold green]\n\n"
                f"  Current:  [dim]{info.current_version}[/dim]\n"
                f"  Latest:   [bold cyan]{info.latest_version}[/bold cyan]\n"
                f"  Download: {info.download_url}\n\n"
                f"  [dim]Run [italic]hive update download[/italic] to upgrade.[/dim]",
                title="HiveOS Update",
                width=64,
            ))
            if info.release_notes:
                console.print("[bold]Release notes:[/bold]")
                console.print(Markdown(info.release_notes[:500]))
            return f"Update available: {info.current_version} → {info.latest_version}"
        else:
            rprint(Panel(
                f"[green]✔ You're on the latest version[/green]  [bold cyan]{info.current_version}[/bold cyan]",
                title="HiveOS Update",
                width=50,
            ))
            return f"Already up-to-date ({info.current_version})"


def _trim_notes(body: str, max_chars: int = 1000) -> str:
    """Trim release notes to a reasonable length for CLI display."""
    if len(body) <= max_chars:
        return body
    return body[:max_chars] + "\n\n… (truncated)"
