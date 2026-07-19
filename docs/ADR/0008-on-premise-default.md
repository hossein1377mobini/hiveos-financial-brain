# ADR-0008: On-Premise Default Deployment

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

HiveOS handles sensitive business data. The Product Bible establishes data sovereignty as a non-negotiable principle. The deployment model must reflect this commitment from day one.

## Decision

HiveOS deploys on customer infrastructure by default. All components run locally. No data leaves customer control unless explicitly configured (cloud AI provider option). Remote access is for management and monitoring only, not for relocating data.

## Rationale

- Data sovereignty is a core product principle. The architecture must enforce it, not just permit it.
- Enterprise and regulated industry customers require on-premise deployment. Building for on-premise first ensures these customers can adopt HiveOS.
- Cloud deployment can be layered on later. On-premise to cloud is a simpler migration than cloud to on-premise.

## Consequences

- Positive: Customers maintain full control of their data.
- Positive: HiveOS works fully offline (no internet dependency for core functionality).
- Negative: Deployment complexity is higher than SaaS (customer must manage infrastructure).
- Negative: Update/distribution mechanism must work for air-gapped environments.

## References

- Product Decisions: PD-08
- Product Bible §9 (Data Sovereignty)
- Product Principles P6 (On-Premise First), P9 (Data Sovereignty)
- AI Provider Specification §4 (local default)
