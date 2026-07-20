# 10 — Security

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/ADR/0013`, `0015`  
> **Dependencies:** 05-Core-Services (RBAC)  
> **Priority:** 6  

---

## Purpose

Security model for HiveOS. Covers authentication, authorization, data isolation, API key management, and audit trail. A developer implementing the API Gateway or Domain Pack Manager reads this for security requirements.

## Scope

**In:** V1 security model (admin/user), authentication mechanism, authorization rules, data isolation (single business), Domain Pack safety, network security (local-only default), audit trail (Execution History), V2+ expansion points.

**Out:** Deployment hardening (11-Deployment), configuration of auth (09-Configuration), service implementation (05-Core-Services).

## Table of Contents

```
1. Threat Model
   1.1 Assets (business data, execution history, knowledge)
   1.2 Threats (data exfiltration, unauthorized execution, pack tampering)
   1.3 Trust Boundaries (Core vs Domain Packs, Local vs Cloud AI)

2. Authentication (V1)
   2.1 API Token (Bearer token, from config or env)
   2.2 Session Cookie (Dashboard, optional)
   2.3 No SSO / LDAP in V1

3. Authorization (V1)
   3.1 Role: admin — can install packs, configure system, ingest knowledge
   3.2 Role: user — can run Skills, run Workflows, search knowledge
   3.3 Single boolean: is_admin
   3.4 No resource-level permissions in V1

4. Data Isolation
   4.1 Single Business per Installation
   4.2 No Multi-Tenancy in V1
   4.3 Domain Packs — read-only, no customer data
   4.4 Organization Knowledge — customer-owned, mutable
   4.5 Execution History — customer-owned, append-only

5. Domain Pack Safety
   5.1 Declarative Only (no executable code)
   5.2 No Network Access from Pack
   5.3 No File System Access outside Pack Directory
   5.4 Installation Validation (schema check, no scripts)

6. Network Security
   6.1 Local-Only Default (bind 127.0.0.1)
   6.2 Cloud AI is Explicit Opt-In
   6.3 No External Dependencies Required

7. API Key Management
   7.1 AI Provider API Keys (cloud adapter)
   7.2 Stored in Config (env var or config file)
   7.3 Not Logged, Not in Execution History

8. Audit Trail
   8.1 Execution History (immutable, append-only)
   8.2 Full Prompt/Response Stored
   8.3 User Actions (pack install, config change) — V2+

9. V2+ Expansion Points
   9.1 Fine-Grained RBAC
   9.2 SSO / OIDC
   9.3 Multi-Tenancy
   9.4 Per-Skill Authorization
   9.5 Signed Domain Packs
```

## Estimated Size

~400 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 05-Core-Services | Core API Gateway implements auth middleware |
| 09-Configuration | Auth token and API keys configured here |
| 11-Deployment | Deployment hardening (firewall, reverse proxy) |
| docs/ADR/0013 | Simplified RBAC in V1 |
| docs/ADR/0015 | Human Ownership of Business Truth |

## Document Boundary Verification

This document defines the SECURITY MODEL (what is allowed, by whom). It does NOT define how auth is implemented in code (05), how deployment hardens the system (11), or where keys are stored (09). Model vs implementation vs deployment — three separate concerns.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |