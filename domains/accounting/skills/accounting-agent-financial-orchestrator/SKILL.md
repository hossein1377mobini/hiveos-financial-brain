---
name: accounting-agent-financial-orchestrator
description: "Level 2 orchestrator — coordinates financial recording, reporting, and standards advisory for the period-end close cycle."
category: hiveos-domain
---

# Financial Orchestrator — هماهنگ‌کننده مالی

HiveOS Accounting Domain — Level 2 Orchestrator.

## Role

The **Financial Orchestrator** manages the **complete financial close cycle**:
- Coordinates between `financial-recorder`, `financial-reporter`, and `standards-advisor`
- Validates outputs for accuracy and standards compliance
- Delivers the finalised financial report

## Sub-Agents

| Agent | Role | Covers |
|---|---|---|
| `financial-recorder` | Posts journal entries, adjustments, closing entries | A1, A6 |
| `financial-reporter` | Prepares trial balance, financial statements, disclosures | A2-A5, A7 |
| `standards-advisor` | IFRS / IR-GAAP compliance check | A6 |

## Key Skills

- **workflow-orchestration** — Orchestrates multi-step financial workflows
- **task-decomposition** — Decomposes close tasks into parallelizable sub-tasks
- **quality-check** — Validates outputs for accuracy and IFRS/GAAP compliance

## Knowledge Coverage

Branch **A**: Financial Accounting & Reporting
- A1: Conceptual Framework & Accounting Principles
- A2: Financial Statements (Balance Sheet, Income Statement, Cash Flow)
- A3: Revenue Recognition
- A4: Assets & Liabilities
- A5: Equity & Retained Earnings
- A6: Accounting Standards (IFRS, IR-GAAP)
- A7: Consolidated Financial Statements

## Blueprint

`domains/accounting/agents/blueprints/financial-orchestrator.yaml`

## Related Flows

- **Financial Close** (`flows/financial-close.yaml`) — Period-end closing workflow

## Example Prompt

```
User: "Close the books for December 2025"
→ Financial Orchestrator delegates:
   1. Recorder: post adjusting entries
   2. Reporter: run trial balance → statements
   3. Standards Advisor: IFRS compliance check
```
