# 09 — Configuration

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Dependencies:** 05-Core-Services (Configuration Service section)  
> **Priority:** 6  

---

## Purpose

Complete Configuration Service specification. Every config key, type, default value, scope, and access pattern. An administrator or operator reads this to configure a HiveOS instance.

## Scope

**In:** Full config key table, config file format, storage location, startup behavior, V2+ expansion points.

**Out:** How config keys are consumed by services (05-Core-Services), product-level configuration philosophy.

## Table of Contents

```
1. Configuration Service
   1.1 Responsibility
   1.2 Access Patterns (read at startup, hot-reload in V2)
   1.3 Config Storage (file in V1, database in V2)

2. Config Key Table
   2.1 ai.provider — "local" | "cloud"
   2.2 ai.local.endpoint — URL (default: "http://localhost:11434/api/generate")
   2.3 ai.local.default_model — string (default: "llama3.1")
   2.4 ai.cloud.endpoint — URL (default: "https://api.openai.com/v1")
   2.5 ai.cloud.api_key — string (V1: from env var or config file)
   2.6 ai.cloud.default_model — string (default: "gpt-4o-mini")
   2.7 ai.parameters.temperature — float (default: 0.3)
   2.8 ai.parameters.max_tokens — integer (default: 4096)
   2.9 knowledge.storage_path — path (default: "~/.hiveos/knowledge")
   2.10 domain.packs_path — path (default: "~/.hiveos/domains")
   2.11 execution.history.storage_path — path (default: "~/.hiveos/history")
   2.12 execution.timeout_seconds — integer (default: 120)
   2.13 server.port — integer (default: 9876)
   2.14 server.host — string (default: "127.0.0.1")
   2.15 auth.token — string (V1: from env var or config)

3. Config File Format
   3.1 YAML Structure
   3.2 Example Config File
   3.3 Environment Variable Overrides

4. V2+ Expansion Points
   4.1 Hot-Reload
   4.2 Per-Business Overrides
   4.3 Config Validation at Write Time
```

## Estimated Size

~300 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 05-Core-Services | Configuration Service consumes and exposes these keys |
| 10-Security | Auth token config relates to security model |
| 11-Deployment | Deployment guide references config keys for setup |

## Document Boundary Verification

This document defines CONFIGURATION (what keys, what defaults). It does NOT define how services access config (05) or how deployment sets config (11). Config definition vs config consumption vs config distribution — three separate concerns.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
