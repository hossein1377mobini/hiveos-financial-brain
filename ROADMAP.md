# HiveOS Roadmap 🗺️

> **Vision:** A Multi-Agent Operating System with a visual Playground, transparent Brain, and pluggable domain knowledge.
>
> **Scope cut (v0.12.0 review):** Stripped 70% — no 3D viz, no license tiers, no multi-tenancy, no audit trails, no pattern recognition. One domain. One user. Ship fast.

---

## ✅ Phase 0-3: Core Infrastructure (Done)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | Foundation (KB, Git, Python pkg, Flow DSL + Validator) | ✅ |
| 1 | Playground CLI (Flow Engine, 3-agent demo, state, error handling) | ✅ |
| 2 | Integration (Hermes subagents, resume, retry, knowledge sync) | ✅ |
| 3 | Packaging (registry, publish, install, remote client) | ✅ |

---

## ✅ Phase 4: Mothership (Core Only)

Simplified — keep routing and bus, drop resilience complexity.

| Component | Description | Status |
|-----------|-------------|--------|
| Agent Registry | Capabilities, heartbeat | ✅ |
| Task Router | 5 strategies | ✅ |
| Communication Bus | Pub/sub, 2 backends | ✅ |
| Mothership Server | FastAPI REST API | ✅ |
| Mothership CLI | agent/route/bus/server | ✅ |

**Removed:** Circuit breaker, health checker, reassignment logic. Agents die → task requeued. Simple.

---

## ✅ Phase 6: Playground — Core APIs

| Code | Feature | Status |
|------|---------|--------|
| P-01 | `POST /api/playground/validate` — Flow YAML validator | ✅ |
| P-02 | `POST /api/playground/auto-agents` — Task → domain agent matching | ✅ |
| P-03 | `GET /api/playground/templates` — Template browser | ✅ |
| P-04 | Visual Canvas (HTML5 Canvas + drag & drop) | ✅ |
| P-05 | Run/Debug + WebSocket streaming | ✅ |

---

## ✅ Phase 7: Brain — Core Engine

| Code | Feature | Status |
|------|---------|--------|
| B-01 | Event Stream Pipeline (agent lifecycle) | ✅ |
| B-02 | Decision Tracer (step-by-step path tracking) | ✅ |
| B-03 | Approval Gate Engine (create/approve/reject/expire) | ✅ |
| B-04 | Brain API (REST) | ✅ |

**Removed:** 3D Neural View (B-05), WebSocket streaming (B-06), interactive exploration (B-07), historical replay (B-08). Brain is a trace log + approval gates. No pretty 3D.

---

## ✅ Phase 8: Learning — Passive Logger Only

| Code | Feature | Status |
|------|---------|--------|
| L-01 | Execution Logger (in-memory collection + stats + trends) | ✅ |

**Removed:** Pattern recognition (L-02), knowledge accumulation (L-04), adaptive routing (L-05). Learning = collect data. Humans analyze later.

---

## ✅ Phase D1: Accounting Domain (One Domain)

| Deliverable | Status |
|-------------|--------|
| Knowledge tree (200+ nodes, 10 branches) | ✅ |
| Domain manifest (29 agents, 6 flows) | ✅ |
| 29 agent blueprints (YAML) | ✅ |
| 6 flow templates (YAML) | ✅ |
| Hermes skills per agent (6 orchestrator SKILL.md) | ✅ |
| Agent auto-generation API | ✅ |
| Template browser API | ✅ |

**No more domains until v2.** One domain proves the model.

---

## ✅ Phase D2: Domain Registry (Minimal)

| Deliverable | Status |
|-------------|--------|
| `hive domain` (list/info/install/remove/init) | ✅ |
| Domain registry (local catalog) | ✅ |

---

## ✅ Phase S: SQLite Persistence

| Code | Feature | Status |
|------|---------|--------|
| S-01 | SQLite StorageEngine | ✅ |
| S-02 | Persist Brain (EventStream, Traces, Gates) | ✅ |
| S-03 | Persist Learning (ExecutionLogs) | ✅ |
| S-04 | Persist Playground (FlowRuns) | ✅ |
| S-05 | Data directory init | ✅ |
| S-06 | Migration system | ✅ |

---

## ✅ Phase CL: Standardisation

| Code | Feature | Status |
|------|---------|--------|
| CL-01 | CHANGELOG.md | ✅ |
| CL-02 | CI (pytest on push) | ✅ |
| CL-03 | Auto-update skeleton | ✅ |

---

## ✅ Phase: Playground UI (React Flow)

| Deliverable | Status |
|-------------|--------|
| Node Palette (4 categories: Trigger/Action/AI/Flow Control) | ✅ |
| React Flow Canvas (snap-to-grid, connections) | ✅ |
| Properties Panel (JSON editor) | ✅ |
| Mini-map & Controls | ✅ |
| Execution Trace panel | ✅ |
| Toolbar (Templates, Run, Clear) | ✅ |
| Execution Visualization (animated shimmer) | ✅ |
| Design Tokens (Linear-inspired dark theme) | ✅ |
| Backend Integration (FastAPI SPA) | ✅ |

---

## ✅ Phase: Desktop & Build

| Deliverable | Status |
|-------------|--------|
| Desktop Shell (pywebview native window) | ✅ |
| PyInstaller → HiveOS.exe | ✅ |
| MSI installer (Inno Setup) | ✅ |
| PWA (manifest, Service Worker, offline fallback) | ✅ |

---

## 🏁 What's Left for v1.0.0

| Priority | Task | Status |
|----------|------|--------|
| 🟡 | Windows code signing (Authenticode) | Needs certificate |
| 🟢 | First GitHub Release (v0.12.0) | Ready to cut |

---

## 📊 Progress Summary

```
Phase 0-3 (Core):           ██████████████████████████ 100%
Phase 4 (Mothership):       ██████████████████████████ 100%
Phase 6-7 (Playground+Brain):████████████████████████████ 100%
Phase 8 (Learning):         ██████████████████████████ 100%
Phase D1-D2 (Domain):       ██████████████████████████ 100%
Phase S (Storage):          ██████████████████████████ 100%
Phase CL (Standardisation): ██████████████████████████ 100%
Playground UI:              ██████████████████████████ 100%
Desktop & Build:            ██████████████████████████ 100%
```

---

## ❌ Features Cut (v0.12.0 Review)

| Feature | Why Cut |
|---------|---------|
| 3D Neural View (Three.js) | Eye candy. Brain traces are enough. |
| License tiers / pricing | No paying users yet. Premature. |
| Multi-tenant workspaces | Single-user product. Add when needed. |
| Audit Trail (JSONL) | Overkill. SQLite logs suffice. |
| RBAC / auth | Single user. No roles to assign. |
| Pattern recognition | Premature ML. Collect data first (L-01). |
| Circuit breaker / health check | Agents die → requeue. Simple wins. |
| Adaptive routing (L-05) | Premature. 5 static strategies work. |
| Knowledge accumulation (L-04) | Premature. Prove one domain first. |
| Historical replay (B-08) | Nice-to-have. Trace logs cover debugging. |
| Interactive exploration (B-07) | Dashboard exists. No need for fancy clicky. |
| WebSocket streaming (B-06) | REST polling works. Add when latency matters. |
| Cross-domain dependencies | One domain. N/A. |
| Remote registry (HTTP) | Local catalog for now. |
