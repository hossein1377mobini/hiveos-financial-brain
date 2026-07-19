# ADR-0013: Simplified RBAC in V1

**Status:** Approved
**Date:** 2026-07-19
**Owner:** Chief Product Architect

## Context

Role-based access control (RBAC) with fine-grained permissions, multiple roles, and resource-level access is a standard enterprise feature. However, V1 targets a single organization with a small team.

## Decision

V1 RBAC is a single boolean: `is_admin`. Admin users can install Domain Packs, manage knowledge, and configure the system. Non-admin users can search knowledge, run Skills, and execute Workflows. No fine-grained permissions, no resource-level access control, no multi-role system.

## Rationale

- V1 has one Business with one small team. Complex RBAC adds weeks of design, implementation, and testing before any customer needs it.
- An `is_admin` flag covers the realistic V1 scenarios (single admin manages the system, team members use it).
- Fine-grained RBAC can be added in V2 without breaking the admin/user model (admin becomes a role, new roles are added).

## Consequences

- Positive: Simple to implement and understand.
- Positive: Reduces V1 scope by an estimated 2-3 weeks of engineering.
- Negative: Not suitable for large organizations with departmental boundaries. This segment is V2+.
- Negative: If a V1 customer grows rapidly, they may hit RBAC limitations before V2 ships.

## References

- Product Decisions: PD-13
- Product Scope: V1 section
- Product Principles P10 (Buildability)
