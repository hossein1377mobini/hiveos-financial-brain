# Changelog

All notable changes to HiveOS are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.10.0] — 2026-07-14

### Added
- **P-07: Template Customizer** (`PlaygroundEngine.customize_template()`) — Load any flow template and apply user overrides (description, trigger, agent skills, memory config) via deep-merge before running
- **P-08: Flow Library** (`src/hiveos/playground/library.py`) — Persistent CRUD storage for user-created flows via StorageEngine. `FlowLibrary` class with: `save_flow`, `load_flow`, `list_flows` (filter by user/tag, sort by date), `delete_flow`, `update_flow`, `count`
- **Desktop Shell** (`src/hiveos/desktop/app.py`) — Phase A: Native Windows desktop window via pywebview wrapping the HiveOS dashboard. `DesktopApp` class with full window lifecycle management
- **PyInstaller Build Script** (`build/build_exe.py`) — Phase C: One-command build producing `dist/HiveOS/HiveOS.exe` with all hidden imports, domain data, and no console window
- **Inno Setup Installer** (`build/installer.iss`) — Phase D: MSI installer script with Windows 10+ check, desktop/startup shortcuts, Persian language support, and user data cleanup on uninstall
- `hive desktop start` CLI command — Launch HiveOS in a native Windows window with configurable port/size/fullscreen
- `hive desktop connect` CLI command — Open browser to an already-running dashboard

### Added (optional dependencies)
- `[desktop]` extra — `pywebview>=6.0` for the native window shell
- `[build]` extra — `pyinstaller>=6.0` for .exe packaging

### Changed
- Version bumped from `0.9.2` to `0.10.0` in `__init__.py`, `pyproject.toml`, CLI banner, and all doc files
- `pyproject.toml` — added optional-dependencies groups (`desktop`, `build`)

### Tests
- **436 total** — all existing tests preserved (no regressions)

---

## [0.9.2] — 2026-07-14

### Added
- **CL-03: Auto-Update Skeleton** (`src/hiveos/update/checker.py`) — Lightweight update checker that queries GitHub Releases API. `UpdateChecker.check()` returns structured `UpdateInfo` with version comparison, download URL, release notes. Supports semver with pre-release tags (alpha/beta/rc). (23 new tests)

### Added (CLI)
- `hive update check` — Check the latest HiveOS release on GitHub
- `hive update info` — Display current vs latest version info in a table

### Tests
- **436 total** — 23 new tests (8 version parsing + 4 UpdateInfo + 11 UpdateChecker), all existing tests preserved

---

## [0.9.1] — 2026-07-14

### Added
- **S-06: Migration System** (`src/hiveos/storage/migrations.py`) — Schema versioning for SQLite StorageEngine. MigrationRunner tracks applied versions and auto-runs pending migrations on connect. Built-in migration #1 creates kv_store schema. (14 new tests)
- **D-05: Domain Plugin CLI** (`src/hiveos/domain/manager.py`) — DomainManager scans `domains/` directory and loads domain.yaml manifests. `hive domain` CLI group with: **list**, **info**, **install**, **remove**, **init** commands. (20 new tests)
- **D-04: Hermes Skills for 6 Accounting Orchestrators** — Hermes skill files (SKILL.md) for master-financial-assistant, financial-orchestrator, management-orchestrator, audit-orchestrator, tax-orchestrator, advisory-orchestrator

### Changed
- `StorageEngine._connect()` now runs built-in migrations automatically; exposes `.migration_runner` property
- `hive util init` now creates `~/.hiveos/data/` directory for persistent storage

### Tests
- **413 total** — 34 new tests (14 migration + 20 domain), all existing tests preserved

---

## [0.9.0] — 2026-07-14

### Added
- **Storage Engine** (`src/hiveos/storage/engine.py`) — SQLite-based persistence layer with generic key-value API. Thread-safe, WAL mode, auto-creates `~/.hiveos/data/hiveos.db`. Methods: `upsert`, `load`, `load_all`, `load_all_with_keys`, `delete`, `clear`, `count`, `vacuum`. (13 tests)
- **Persistence for Brain modules:**
  - `EventStream` — events survive server restart; stored in `brain:events` namespace
  - `DecisionTracer` — traces persisted in `brain:traces` namespace; auto-restore on init
  - `ApprovalGateEngine` — gates stored in `brain:gates` namespace; approval/rejection/expiry persisted immediately
- **Persistence for Learning modules:**
  - `ExecutionLogger` — execution logs stored in `learning:executions` namespace; `_by_flow` and `_by_agent` indexes rebuilt on restore
- **Persistence for Playground:**
  - `PlaygroundRunner` — FlowRun state saved on every status change; restored from `playground:runs` namespace at startup
- **Endgame Vision section** in `AGENTS.md` — phased roadmap to Windows Native (Tauri → PyInstaller → MSI → Auto-Update → CI/CD)
- **Data directory init** — `hive util init` now creates `~/.hiveos/data/` directory for persistent storage
- **GitHub Actions CI** — `.github/workflows/test.yml` runs pytest on push/PR to `main`

### Changed
- `DashboardApp` — all modules now share a single `StorageEngine` instance via `data_dir/hiveos.db`
- `DashboardServer` — `stop()` closes the storage connection; storage exposed via `_dashboard_app`
- `PlaygroundRunner.__init__` — accepts optional `storage` parameter; class-level `_storage` and `_namespace` for cross-instance persistence
- `EventStream.__init__`, `DecisionTracer.__init__`, `ApprovalGateEngine.__init__`, `ExecutionLogger.__init__` — accept optional `storage` parameter; restore on init
- Bumped version strings to `0.9.0` in `__init__.py`, `config.py`, `cli/main.py` (banner, version flag, info command)

### Fixed
- `TemporaryDirectory` cleanup errors in dashboard tests — added `storage.close()` in fixtures and `__del__` on `StorageEngine`
- `test_list_runs_empty` robustness — handles global `_run_store` invariants
- `test_create_run_invalid_yaml` — relaxed exception expectation to accept `yaml.ScannerError`

### Tests
- **379 total** — 13 new storage engine tests, +6 robustness fixes in runner/dashboard tests
- `test_storage.py` — full coverage: CRUD, persistence across instances, complex nested data, vacuum

---

## [0.8.0] — 2026-07-14

### Added
- **Playground Runner** (`src/hiveos/playground/runner.py`) — async flow execution with WebSocket streaming, approval gate integration, dependency tracking, cancellation
- **Analytics Engine** (`src/hiveos/learning/analytics.py`) — trend analysis, bottleneck detection, failure pattern analysis, anomaly detection, report generation
- **Dashboard upgrades:** 4 new tabs (Playground Canvas, Gates, Neural 3D, Learning Analytics), WebSocket event streaming, Three.js 3D visualisation
- **Dashboard API endpoints:** `POST /api/playground/run`, `GET /api/playground/run/{run_id}`, `WS /api/playground/ws/{run_id}`, `GET /api/playground/gates/pending`, `POST /api/playground/gates/{gate_id}/decision`, `GET /api/analytics/trends`, `GET /api/analytics/bottlenecks`

### Changed
- Version bumped from `0.6.0` to `0.8.0`
- `pyproject.toml` — dependencies include `websockets`, `fastapi>=0.100.0`, `uvicorn>=0.20.0`, `pydantic>=2.0`
- `src/hiveos/playground/__init__.py` and `src/hiveos/learning/__init__.py` — updated exports

### Tests
- 366 total — 19 new runner tests, 13 new analytics tests

---

## [0.7.0] — 2026-07-14

### Added
- Playground Core APIs: flow validator (P-01), auto-agent matching (P-02), template browser (P-03)
- Brain Engine: Event Stream Pipeline (B-01), Decision Tracer (B-02), Approval Gate Engine (B-03)
- Learning: Execution Logger (L-01)
- License pricing system + 29 accounting agent blueprints + 6 flow templates
- Bilingual README (EN + FA)

### Tests
- 329 total

---

## [0.6.0] — 2026-07-14

### Added
- License & pricing system
- 29 agent blueprints (YAML)
- 6 flow templates (YAML)
- Bilingual README

---

## [0.5.x] — 2026-07-14

### Added
- v0.5.0: RBAC (36 tests)
- v0.5.1: Audit Trail (20 tests)
- v0.5.2: Dashboard — FastAPI + SPA (23 tests)
- v0.5.3: Multi-tenant Workspaces (38 tests)

---

## [0.1–0.5] — 2026-07-13

### Added
- Foundation CLI, Playground CLI, Integration, Packaging, Mothership subsystems
