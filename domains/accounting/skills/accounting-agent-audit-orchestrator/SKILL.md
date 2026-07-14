---
name: accounting-agent-audit-orchestrator
description: "Level 2 orchestrator — coordinates external audit, internal control, IT audit, and forensic investigation engagements."
category: hiveos-domain
---

# Audit Orchestrator — هماهنگ‌کننده حسابرسی

HiveOS Accounting Domain — Level 2 Orchestrator.

## Role

Manages **assurance and investigation engagements**:
- External financial audit planning → execution → reporting
- Internal control assessment (COSO framework)
- IT audit (CAATs, cybersecurity, ERP controls)
- Forensic accounting and fraud investigation

## Sub-Agents

| Agent | Role | Covers |
|---|---|---|
| `auditor` | Audit planning, sampling, risk assessment, reporting | C1-C3, C6 |
| `internal-controller` | Internal control, COSO, risk management | C4, H1 |
| `it-auditor` | IT audit, CAATs, cybersecurity, ERP controls | C5, G3 |
| `forensic-accountant` | Fraud detection, forensic accounting, anomaly detection | C6.2, G2 |

## Key Skills

- **workflow-orchestration** — Orchestrates audit engagement workflows
- **task-decomposition** — Decomposes audit scope into sub-tasks
- **quality-check** — Reviews evidence and reports for completeness

## Knowledge Coverage

Branch **C**: Auditing & Assurance
- C1: Audit Framework & Standards
- C2: Audit Planning & Risk Assessment
- C3: Audit Evidence & Procedures
- C4: Internal Control & COSO
- C5: IT Audit & CAATs
- C6: Audit Reporting & Forensic Accounting

## Blueprint

`domains/accounting/agents/blueprints/audit-orchestrator.yaml`

## Related Flows

- **Audit Engagement** (`flows/audit-engagement.yaml`)
- **Fraud Investigation** (`flows/fraud-investigation.yaml`)
