# Decision #001: Memory Storage Structure

**Date:** 2026-07-13
**Status:** ✅ Accepted
**Tags:** `#memory` `#architecture` `#storage`

---

## Problem

The HiveOS product needs a dedicated memory/knowledge base that can grow with the product, is portable, version-controlled, and enterprise-grade.

## Decision

Use a file-based directory (`docs/`) with:
- Numbered prefixes for ordered browsing
- Markdown format for universal compatibility
- Git for version control
- `.obsidian/` config for Obsidian compatibility

### File Naming Convention

| Pattern | Example | Purpose |
|---------|---------|---------|
| `NN-title.md` | `01-product-vision.md` | Ordered docs (Vision, Architecture, etc.) |
| `YYYY-MM-DD-title.md` | `2026-07-13-kickoff.md` | Meeting notes by date |
| `NNN-title.md` | `001-use-file-based-memory.md` | ADRs and decisions |

### Index Files

Every folder has an `_index.md` as a table of contents.

## Tags Convention

Every doc begins with a YAML-like header block:

```markdown
# Title
**Date:** 2026-07-13
**Tags:** `#tag1` `#tag2`
```
