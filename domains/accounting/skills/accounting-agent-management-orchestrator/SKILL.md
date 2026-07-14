---
name: accounting-agent-management-orchestrator
description: "Level 2 orchestrator — coordinates cost analysis, budgeting, performance measurement, and strategic advisory."
category: hiveos-domain
---

# Management Orchestrator — هماهنگ‌کننده مدیریت

HiveOS Accounting Domain — Level 2 Orchestrator.

## Role

Coordinates **management accounting** workflows:
- Cost analysis and allocation
- Budget preparation and forecasting
- Performance measurement (Balanced Scorecard, KPIs)
- Strategic planning and competitive analysis

## Sub-Agents

| Agent | Role | Covers |
|---|---|---|
| `cost-analyst` | Costing, variance analysis, CVP, ABC | B1, B3, B6 |
| `budget-planner` | Budgeting, forecasting, capital budgeting | B2, B4 |
| `performance-advisor` | Balanced scorecard, value chain | B4, B5 |
| `strategy-advisor` | Competitive/industry analysis, strategic planning | I3, I4, B5 |

## Key Skills

- **workflow-orchestration** — Management accounting workflow orchestration
- **task-decomposition** — Breaks management queries into specialist tasks
- **quality-check** — Reviews reports for internal consistency

## Knowledge Coverage

Branch **B**: Management Accounting & Control
- B1: Cost Concepts & Classification
- B2: Budgeting & Forecasting
- B3: Cost-Volume-Profit Analysis
- B4: Performance Measurement
- B5: Strategic Management Accounting
- B6: Activity-Based Costing

## Blueprint

`domains/accounting/agents/blueprints/management-orchestrator.yaml`

## Related Flows

- **Annual Budget Preparation** (`flows/annual-budget.yaml`)
