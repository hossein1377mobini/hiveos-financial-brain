"""HiveOS V2 Dashboard — FastAPI application factory.

Creates the FastAPI app that serves both the REST API and the embedded
single-page dashboard UI.  Wires together:
    ConfigService → StorageEngine → KnowledgeService → DomainRegistry
                                         ↓
                                  API route modules
                                         ↓
                                  Static HTML/JS/CSS

Auth: Every route is protected by default via AuthChecker (RBAC Bearer
token).  Public routes (/, /api/health) are explicitly exempt.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends

from hiveos.knowledge import KnowledgeService
from hiveos.storage import StorageEngine
from hiveos.privacy import PrivacyConfig, PrivacyAuditTrail, PrivacyGuard
from .config_service import ConfigService

# Resolve paths
_HERE = Path(__file__).parent
_STATIC = _HERE / "static"


def create_app() -> FastAPI:
    """uvicorn entry-point factory: ``uvicorn hiveos.dashboard.app:create_app --factory``."""
    app_inst = HiveOSApp()
    return app_inst.api


class HiveOSApp:
    """Application bootstrap — wires services and creates the FastAPI app."""
    
    def __init__(self, config_path: Optional[Path] = None):
        # 1. Config (respect HIVEOS_DATA_DIR env for Docker)
        self.config = ConfigService(config_path)
        
        # 2. Storage — honour HIVEOS_DATA_DIR env override
        data_dir_env = os.environ.get("HIVEOS_DATA_DIR")
        if data_dir_env:
            data_dir = Path(data_dir_env)
            db_path = data_dir / "hiveos.db"
        else:
            db_path = Path(self.config.get("storage.db_path", "~/.hiveos/data/hiveos.db")).expanduser()
            data_dir = Path(self.config.get("storage.data_dir", "~/.hiveos/data")).expanduser()
        
        self.storage = StorageEngine(db_path)
        
        # 3. Privacy Configuration (ADR-0017: Privacy-First)
        privacy_config_path = data_dir / "privacy.json"
        self.privacy_config = PrivacyConfig.load(privacy_config_path)
        
        # Privacy audit trail
        self.privacy_audit = PrivacyAuditTrail(data_dir / "privacy_audit.db")
        
        # Privacy guard (intercept external HTTP calls)
        self.privacy_guard = PrivacyGuard(self.privacy_config)
        
        # 4. Knowledge
        self.knowledge = KnowledgeService(self.storage)
        
        # 5. Domain Registry
        from hiveos.domain.registry import DomainRegistry
        
        domains_root = data_dir / "domains"
        if not domains_root.exists():
            # Fall back to project-level domains
            project_domains = _HERE.parent.parent.parent.parent / "domains"
            if project_domains.exists():
                domains_root = project_domains
        self.domain_registry = DomainRegistry(
            storage=self.storage, domains_root=domains_root
        )
        self.domain_registry.scan()
        
        # 6. Execution logger
        from hiveos.learning.logger import ExecutionLogger
        self.execution_logger = ExecutionLogger(storage=self.storage)
        
        # 7. RBAC + Audit (for auth middleware)
        from hiveos.rbac import RBACManager
        from hiveos.audit import AuditTrail
        
        self.rbac = RBACManager(data_dir=data_dir)
        self.audit = AuditTrail(data_dir=data_dir / "audit")
        
        # 8. Auth checker
        from .auth import AuthChecker
        self._auth_checker = AuthChecker(rbac=self.rbac, audit=self.audit)
        
        # 9. File Watch Service
        from hiveos.filewatch import FileWatchService
        self.filewatch = FileWatchService(self.storage, self.knowledge)
        
        # 10. Build FastAPI app
        self._app = self._build_app()

    @property
    def api(self) -> FastAPI:
        return self._app

    def _build_app(self) -> FastAPI:
        host = self.config.get("server.host", "127.0.0.1")
        port = self.config.get("server.port", 8420)
        
        app = FastAPI(
            title="HiveOS Dashboard",
            version="2.0.0",
            description="HiveOS V2 — Developer/Debug Console",
        )
        
        # ── CORS (restrict to localhost by default) ─────────────────
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://127.0.0.1:8080",
                "http://localhost:8080",
                "http://127.0.0.1:8420",
                "http://localhost:8420",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # ── Privacy Middleware (ADR-0017) ──────────────────────────
        from .routes.privacy import router as privacy_router
        from .routes import deps as _deps
        _deps.set_auth_deps(self._auth_checker)
        
        # Wire privacy deps
        _deps.set_privacy_deps(self.privacy_config, self.privacy_audit)

        # ── Wire route modules ─────────────────────────────────────
        from .routes import knowledge, domain_packs, skills, workflows, history, config, filewatch

        # Pass service deps
        knowledge.set_knowledge_service(self.knowledge)
        domain_packs.set_domain_registry(self.domain_registry)
        skills.set_services(self.domain_registry, self.execution_logger)
        workflows.set_services(self.domain_registry, self.execution_logger)

        # V1.5: Workflow editing service
        from .workflow_service import WorkflowService
        self.workflow_service = WorkflowService(self.domain_registry)
        workflows.set_workflow_service(self.workflow_service)
        history.set_execution_logger(self.execution_logger)
        config.set_config_service(self.config)

        app.include_router(knowledge.router)
        app.include_router(domain_packs.router)
        app.include_router(skills.router)
        app.include_router(workflows.router)
        app.include_router(history.router)
        app.include_router(config.router)
        app.include_router(privacy_router)
        
        filewatch.set_filewatch_service(self.filewatch)
        app.include_router(filewatch.router)

        # ── Public endpoints (no auth) ─────────────────────────────

        @app.get("/api/health")
        async def health():
            return {
                "status": "ok",
                "version": "2.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # ── Serve static dashboard UI ──────────────────────────────
        if _STATIC.exists():
            app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

        # ── Lifecycle: start file watchers ──────────────────────────
        @app.on_event("startup")
        async def _start_filewatch():
            self.filewatch.start_all()

        @app.get("/", response_class=HTMLResponse)
        async def index():
            html_path = _STATIC / "index.html"
            if html_path.exists():
                return HTMLResponse(html_path.read_text(encoding="utf-8"))
            return HTMLResponse("<h1>HiveOS Dashboard</h1><p>UI not built.</p>")

        return app

    # ── Lifecycle (for embedded use) ────────────────────────────────
    def shutdown(self):
        """Shutdown application and cleanup resources."""
        # Uninstall privacy guard
        if hasattr(self, "privacy_guard"):
            self.privacy_guard.uninstall()
        
        if self.storage:
            self.storage.close()
        if hasattr(self, "filewatch"):
            self.filewatch.stop_all()
