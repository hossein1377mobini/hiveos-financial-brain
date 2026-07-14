"""
HiveOS Desktop Shell — wraps the HiveOS dashboard in a native Windows window.

Phase A of the Windows Native roadmap:
  FastAPI (backend) + pywebview (native window) = desktop app with no browser tabs.

Usage:
    python -m hiveos.desktop.app           # standalone
    hive desktop start                      # via HiveOS CLI
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hiveos.desktop")

# Lazy imports — pywebview may be absent in server-only deployments
_webview: Optional[type] = None


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


class DesktopApp:
    """Manages the native desktop window lifecycle.

    The FastAPI dashboard server runs on a background thread,
    and pywebview renders it in a native Windows window.

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
    ):
        _import_webview()

        self.host = host
        self.port = port
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.debug = debug
        self.data_dir = data_dir or str(Path.home() / ".hiveos" / "data")

        # Dashboard server instance (created lazily)
        self._server = None
        self._httpd = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the dashboard server and open the native window.

        Blocks until the window is closed.
        """
        server_thread = self._start_server()
        url = f"http://{self.host}:{self.port}"

        logger.info("Opening HiveOS desktop window → %s", url)
        window = _webview.create_window(
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

        # Start the GUI event loop (blocks until window closes)
        _webview.start(debug=self.debug, http_server=False)

        # Window closed — shut down the server
        logger.info("Desktop window closed, shutting down...")
        if self._server:
            self._server.stop()

        server_thread.join(timeout=10)

    def run_async(self) -> None:
        """Start the server and window, but return immediately.

        Useful when called from the CLI which runs its own loop.
        """
        self._start_server()
        url = f"http://{self.host}:{self.port}"
        logger.info("Opening HiveOS desktop window → %s", url)
        _webview.create_window(
            self.title,
            url,
            width=self.width,
            height=self.height,
            fullscreen=self.fullscreen,
            resizable=True,
        )

    def stop(self) -> None:
        """Stop the dashboard server and destroy the window."""
        if _webview and _webview.active_window():
            _webview.active_window().destroy()
        if self._server:
            self._server.stop()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _start_server(self) -> threading.Thread:
        """Start the FastAPI dashboard on a background thread."""
        from hiveos.dashboard import DashboardServer
        from hiveos.dashboard.server import DashboardApp

        data_path = Path(self.data_dir)
        data_path.mkdir(parents=True, exist_ok=True)

        server = DashboardServer(
            host=self.host,
            port=self.port,
            app=DashboardApp(data_dir=data_path),
        )

        def _run():
            logger.info("Dashboard server starting on %s:%s", self.host, self.port)
            server.start(background=False)

        thread = threading.Thread(target=_run, daemon=True, name="hiveos-dashboard")
        thread.start()

        self._server = server
        return thread


# ── Standalone entry point ────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = DesktopApp()
    app.run()
