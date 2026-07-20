# 11 — Deployment

> **Version:** 1.0.0  
> **Owner:** Principal Software Architect  
> **Status:** Draft (Phase 1 — Outline)  
> **Last Updated:** 2026-07-19  
> **Upstream Sources:** `docs/ADR/0008`  
> **Dependencies:** 09-Configuration, 10-Security  
> **Priority:** 7  

---

## Purpose

On-premise deployment guide for HiveOS. Covers hardware requirements, installation methods, configuration, verification, and upgrade. A system administrator or devops engineer reads this to deploy HiveOS.

## Scope

**In:** Minimum hardware requirements, installation methods (Docker recommended, native as alternative), step-by-step installation, initial configuration, verification (health check), upgrade procedure, backup/restore, troubleshooting.

**Out:** Configuration key details (09-Configuration), security hardening details (10-Security), product-level deployment philosophy.

## Table of Contents

```
1. Hardware Requirements
   1.1 Minimum Requirements (CPU, RAM, Disk)
   1.2 Recommended Requirements (with local AI)
   1.3 Supported Platforms

2. Installation Methods
   2.1 Docker (Recommended)
       2.1.1 Docker Compose Setup
       2.1.2 Image Tags and Versions
       2.1.3 Volume Mounts
       2.1.4 Network Configuration
   2.2 Native Installation
       2.2.1 Prerequisites (Python, uv)
       2.2.2 Install Steps
       2.2.3 Virtual Environment

3. Configuration
   3.1 Config File Location
   3.2 Required Configs
   3.3 Optional Configs
   3.4 Environment Variable Overrides

4. Verification
   4.1 Health Check
   4.2 Smoke Test (run a Skill)
   4.3 Log Verification

5. Upgrade Procedure
   5.1 Backup Before Upgrade
   5.2 Version Compatibility
   5.3 Upgrade Steps
   5.4 Rollback Procedure

6. Backup and Restore
   6.1 What to Backup
   6.2 Backup Procedure
   6.3 Restore Procedure

7. Troubleshooting
   7.1 Health Check Shows Down
   7.2 AI Provider Not Responding
   7.3 Domain Pack Installation Fails
   7.4 Knowledge Index Corrupted
```

## Estimated Size

~500 lines

## Cross-References

| Target | Relationship |
|--------|-------------|
| 09-Configuration | Deployment sets configuration per these keys |
| 10-Security | Deployment hardening (network binding, TLS) |
| docs/ADR/0008 | On-premise default deployment |

## Document Boundary Verification

This document defines DEPLOYMENT (how to install and run). It does NOT define what configuration keys exist (09) or what the security model is (10). Deployment procedure vs configuration definition vs security model — three separate concerns.

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0.0 | 2026-07-19 | Principal Software Architect | Phase 1 outline |
