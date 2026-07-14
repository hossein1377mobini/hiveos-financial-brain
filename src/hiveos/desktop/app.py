"""
HiveOS Desktop Shell — wraps the HiveOS dashboard in a native Windows window
with auto-update checking on startup.

Phase A + Phase E (Auto-update) of the Windows Native roadmap.

Usage:
    python -m hiveos.desktop.app           # standalone
    hive desktop start                      # via HiveOS CLI
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger("hiveos.desktop")

# Lazy imports — pywebview may be absent in server-only deployments
_webview: Optional[type] = None

GITHUB_API = "https://api.github.com/repos/hossein1377mobini/hiveos-financial-brain/releases/latest"
UPDATE_CHECK_TIMEOUT = 5


def _import_webview():
    global _webview
    try:
        import webview
        _webview = webview
    except ImportError:
        print(
            "pywebview is not installed. Run: uv pip install pywebview",
            file=sys.stderr,
        )
        sys.exit(1)


def _get_current_version() -> str:
    """Read the version from the installed hiveos package."""
    try:
        from hiveos import __version__
        return __version__
    except ImportError:
        return "0.0.0"


def _parse_version(ver: str) -> tuple:
    """Parse semver into comparable tuple (major, minor, patch)."""
    import re
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", ver.strip())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _check_update() -> dict:
    """Check GitHub for a newer release. Returns a dict with update info."""
    try:
        req = Request(
            GITHUB_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "HiveOS/desktop",
            },
        )
        with urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_tag = data.get("tag_name", "").lstrip("v")
        download_url = data.get("html_url", "")
        body = (data.get("body", "") or "")[:500]

        current = _get_current_version()
        latest_parsed = _parse_version(latest_tag)
        current_parsed = _parse_version(current)

        if latest_parsed > current_parsed:
            return {
                "update_available": True,
                "current_version": current,
                "latest_version": latest_tag,
                "download_url": download_url,
                "release_notes": body,
                # Try to find the MSI asset
                "msi_url": _find_msi_asset(data.get("assets", [])),
            }
        return {"update_available": False, "current_version": current}
    except Exception as exc:
        logger.debug("Update check failed: %s", exc)
        return {"update_available": False, "current_version": _get_current_version(), "error": str(exc)}


def _find_msi_asset(assets: list) -> Optional[str]:
    """Find the MSI installer asset URL in GitHub release assets."""
    for asset in assets:
        name = (asset.get("name") or "").lower()
        if name.endswith(".msi") or name.endswith(".exe"):
            # Prefer MSI over exe
            if name.endswith(".msi"):
                return asset.get("browser_download_url")
    for asset in assets:
        name = (asset.get("name") or "").lower()
        if name.endswith(".exe"):
            return asset.get("browser_download_url")
    return None


def _download_and_install(msi_url: str, window) -> None:
    """Download the installer and run it."""
    import tempfile
    try:
        window.load_url("about:blank")  # Show loading state
        window.set_title("HiveOS — Downloading Update...")

        # Download to temp
        tmp_dir = Path(tempfile.gettempdir()) / "hiveos-update"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        installer_path = tmp_dir / "HiveOS-Setup.exe"

        logger.info("Downloading update from %s → %s", msi_url, installer_path)
        window.evaluate_js(
            f'document.body.innerHTML=`<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#0f1117;color:#e8eaf0;font-family:sans-serif;flex-direction:column;gap:16px;"><h2>⬇️ Downloading update...</h2><p style="color:#8b90a5;">This may take a moment.</p></div>`'
        )

        req = Request(msi_url, headers={"User-Agent": "HiveOS/desktop"})
        with urlopen(req, timeout=120) as resp:
            with open(installer_path, "wb") as f:
                shutil.copyfileobj(resp, f)

        logger.info("Download complete: %s", installer_path)
        window.evaluate_js(
            f'document.body.innerHTML=`<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#0f1117;color:#e8eaf0;font-family:sans-serif;flex-direction:column;gap:16px;"><h2>🚀 Installing update...</h2><p style="color:#8b90a5;">The installer will open shortly.</p></div>`'
        )
        time.sleep(1)

        # Run the installer silently
        if installer_path.suffix == ".msi":
            subprocess.Popen(
                ["msiexec", "/i", str(installer_path), "/qb"],
                shell=True,
            )
        else:
            subprocess.Popen([str(installer_path), "/VERYSILENT", "/SUPPRESSMSGBOXES"], shell=True)

        # Close the current app so the installer can update files
        window.destroy()

    except Exception as exc:
        logger.error("Download/install failed: %s", exc)
        window.evaluate_js(
            f'document.body.innerHTML=`<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#0f1117;color:#e8eaf0;font-family:sans-serif;flex-direction:column;gap:16px;"><h2>❌ Update failed</h2><p style="color:#f87171;">{exc}</p><button onclick="location.reload()" style="background:#f5b723;color:#000;padding:10px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:600;">Reload</button></div>`'
        )


class DesktopApp:
    """Manages the native desktop window lifecycle with auto-update support.

    The FastAPI dashboard server runs on a background thread,
    and pywebview renders it in a native Windows window.

    On startup, checks GitHub Releases for a newer version and
    prompts the user to update if one is available.

    Example::

        app = DesktopApp(port=9876)
        app.run()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9876,
        title: str = "HiveOS",
        width: int = 1280,
        height: int = 800,
        data_dir: Optional[str] = None,
        fullscreen: bool = False,
        debug: bool = False,
        check_updates: bool = True,
    ):
        _import_webview()

        self.host = host
        self.port = port
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.debug = debug
        self.check_updates = check_updates
        self.data_dir = data_dir or str(Path.home() / ".hiveos" / "data")

        self._server = None
        self._window = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the dashboard server and open the native window.

        Blocks until the window is closed.
        """
        server_thread = self._start_server()
        url = f"http://{self.host}:{self.port}"

        # Wait for server to be ready
        self._wait_for_server(url)

        logger.info("Opening HiveOS desktop window → %s", url)
        self._window = _webview.create_window(
            self.title,
            url,
            width=self.width,
            height=self.height,
            fullscreen=self.fullscreen,
            resizable=True,
            minimizable=True,
            maximizable=True,
            confirm_close=True,
        )

        # Check for updates in background (after window opens)
        if self.check_updates:
            self._check_for_updates_async()

        # Start the GUI event loop (blocks until window closes)
        _webview.start(debug=self.debug, http_server=False)

        # Window closed — shut down the server
        logger.info("Desktop window closed, shutting down...")
        if self._server:
            self._server.stop()
        server_thread.join(timeout=10)

    def stop(self) -> None:
        """Stop the dashboard server and destroy the window."""
        if _webview and _webview.active_window():
            _webview.active_window().destroy()
        if self._server:
            self._server.stop()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _wait_for_server(self, url: str, max_retries: int = 30) -> None:
        """Wait until the dashboard server is reachable."""
        from urllib.request import urlopen
        for i in range(max_retries):
            try:
                with urlopen(f"{url}/", timeout=2):
                    return
            except Exception:
                time.sleep(1)
        logger.warning("Server did not respond in time, starting window anyway")

    def _start_server(self) -> threading.Thread:
        """Start the FastAPI dashboard on a background thread."""
        from hiveos.dashboard import DashboardServer
        from hiveos.storage import StorageEngine

        data_path = Path(self.data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        db_storage = StorageEngine(data_path / "hiveos.db")

        server = DashboardServer(
            host=self.host,
            port=self.port,
            data_dir=data_path,
            storage=db_storage,
        )

        def _run():
            logger.info("Dashboard server starting on %s:%s", self.host, self.port)
            server.start()

        thread = threading.Thread(target=_run, daemon=True, name="hiveos-dashboard")
        thread.start()
        self._server = server
        return thread

    def _check_for_updates_async(self) -> None:
        """Check for updates in a background thread and prompt user."""

        def _check():
            time.sleep(2)  # Let the UI load first
            try:
                info = _check_update()
                if info.get("update_available"):
                    self._prompt_update(info)
            except Exception as exc:
                logger.debug("Background update check error: %s", exc)

        thread = threading.Thread(target=_check, daemon=True, name="hiveos-update-check")
        thread.start()

    def _prompt_update(self, info: dict) -> None:
        """Show a native confirmation dialog for update."""
        msg = (
            f"A new version of HiveOS is available!\n\n"
            f"Current:  v{info['current_version']}\n"
            f"Latest:   v{info['latest_version']}\n\n"
            f"Download and install now?"
        )

        if self._window and hasattr(self._window, "create_confirmation_dialog"):
            confirmed = self._window.create_confirmation_dialog(
                "HiveOS Update Available",
                msg,
            )
        else:
            # Fallback: use JS confirm dialog
            confirmed = self._window.evaluate_js(
                f"confirm(`{msg}`)"
            ) if self._window else False

        if confirmed:
            msi_url = info.get("msi_url") or info.get("download_url")
            if msi_url:
                _download_and_install(msi_url, self._window)
            else:
                # Open the release page in browser
                webbrowser.open(info.get("download_url", ""))


# ── Standalone entry point ────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = DesktopApp()
    app.run()
