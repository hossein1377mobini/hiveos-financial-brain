# HiveOS Roadmap

> **Vision:** Organizational Intelligence Platform
> **Principle:** HiveOS learns from organizations, reasons on their knowledge, and helps managers make better decisions.
> **Source:** ADR-0017 (Product Direction Update)

---

## V1 — Core Intelligence Platform (NOW)

> "Your organization's knowledge, made computable from day one."

### V1 Scope

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | Domain Pack System | Install, enable, disable, remove Domain Packs | ✅ |
| 2 | Knowledge Retrieval | Unified search index across Domain + Organization knowledge | ✅ |
| 3 | Workflow Execution | Run pre-built Workflow Templates | ✅ |
| 4 | First-Time Experience | After install, show: "These are the business processes we know" | 🟡 |
| 5 | Capability Selection | Customer chooses which capabilities to activate | 🟡 |
| 6 | Customer File Watch | Folder for customer documents, auto-detect new files | 🟡 |
| 7 | Organizational Learning | Parse customer files → build knowledge graph → memory | 🔴 |
| 8 | Privacy-First Architecture | All data stays on customer infrastructure | ✅ |
| 9 | Monitoring Dashboard | Basic status, execution history, alerts | 🟡 |
| 10 | Simple Installer | MSI + PyInstaller for Windows | ✅ |
| 11 | Domain Pack Download | Download from company website/registry | ✅ |

### V1 NOT Included
- Model training / fine-tuning / LoRA
- Custom Workflow creation
- Pattern detection
- Analysis engine
- Recommendation engine
- Multi-domain orchestration
- Enterprise SSO / LDAP
- Two-way system integrations

---

## V1.5 — Decision Support Foundation (NEXT)

> "Helping managers see what's happening."

| # | Feature | Description |
|---|---------|-------------|
| 1 | Organization Variables Wizard | Collect: departments, approval hierarchy, cost centers, suppliers |
| 2 | Auto-Detect Variables | Extract organization-specific info from customer documents |
| 3 | Workflow Customization (Edit) | Modify existing workflow templates (change parameters, steps) |
| 4 | Simple Decision Support | Status alerts, bottleneck detection, delayed approvals |
| 5 | Monitoring Enhancements | Real-time dashboards, KPI tracking |

---

## V2 — Intelligence Layer (FUTURE)

> "The system learns how your organization works."

| # | Feature | Description |
|---|---------|-------------|
| 1 | Analysis Engine | Pattern detection, anomaly detection, trend analysis |
| 2 | Recommendation Engine | Proactive suggestions based on execution history |
| 3 | Custom Workflow Creation | Build new workflows from scratch or from patterns |
| 4 | Advanced Organizational Learning | Cross-file learning, behavior pattern extraction |
| 5 | Decision Support Framework | Generic framework across all Domain Packs |
| 6 | Multiple Domain Packs | Install and orchestrate multiple packs |

---

## V3 — Autonomous Intelligence (LONG TERM)

> "An organization that never forgets and continuously improves."

| # | Feature | Description |
|---|---------|-------------|
| 1 | Proactive Insights | System surfaces insights without user asking |
| 2 | Predictive Analytics | Forecast trends, risks, opportunities |
| 3 | Cross-Organization Learning | Anonymized pattern sharing across opt-in customers |
| 4 | Full Autonomy Mode | Configure autonomy level per Skill/Workflow |
| 5 | Domain Pack Marketplace | Third-party authors |

---

## 4-Engine Architecture

```
Knowledge Engine → Learning Engine → Reasoning Engine → Decision Engine
     ↓                    ↓                ↓                 ↓
Domain Packs         Parse Files      RAG + AI Models    Alerts + Insights
Org Knowledge        Build Memory     Reasoning          Recommendations
                     Update Daily     Context            Action Items
```

| Engine | V1 | V1.5 | V2 | V3 |
|--------|----|----|----|-----|
| Knowledge Engine | ✅ | ✅ | ✅ | ✅ |
| Learning Engine | 🟡 Basic | ✅ | ✅ | ✅ |
| Reasoning Engine | ✅ | ✅ | ✅ | ✅ |
| Decision Engine | ❌ | 🟡 Alerts | ✅ Analysis | ✅ Full |

---

## Key Metrics

| Metric | V1 Target | V1.5 Target | V2 Target |
|--------|-----------|-------------|-----------|
| Time to first insight | < 5 min | < 3 min | < 1 min |
| Customer files processed | 10+ | 50+ | 100+ |
| Workflows available | 6 (accounting) | 12 | 30+ |
| Decision support alerts | 0 | 5 types | 20+ |
| Active users | 1 | 5 | 50+ |

---

## Change History

| Version | Date | Change |
|---------|------|--------|
| 2.0.0 | 2026-07-24 | Complete rewrite — 5-Pillar to 4-Engine model (ADR-0017) |
| 1.0.0 | 2026-07-19 | Initial roadmap |
