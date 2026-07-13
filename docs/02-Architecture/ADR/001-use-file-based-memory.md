# ADR 001: Use File-Based Memory for Product Knowledge Base

## Status
✅ Accepted (2026-07-13)

## Context
The HiveOS product needs a dedicated memory/knowledge base that:
- Stores all product decisions, conversations, and research
- Is accessible daily for ongoing work
- Can be version-controlled and portable
- Is enterprise-grade (traceable, auditable)
- Works with the user's existing Obsidian workflow

## Decision
Use a **file-based markdown directory** (this `docs/` folder) as the primary product knowledge base, structured with numbered prefixes for ordered navigation and Obsidian compatibility.

## Consequences

### Positive
+ Version-controllable with Git (every change is traceable)
+ Portable — drag-and-drop to any machine, open in any markdown editor
+ Works natively with Obsidian (the user's existing tool)
+ No vendor lock-in (not tied to any memory provider)
+ Easy to search (ripgrep, FTS5 via session_search)
+ Can be packaged as part of the product distribution

### Negative
- Requires manual discipline to keep updated
- No built-in real-time sync (though Git push/pull covers this)
- Less suitable for high-frequency writes (better for structured documentation)

## Alternatives Considered

1. **Mem0 / Honcho** — dedicated memory backends, but not portable as file system
2. **Database (SQLite)** — not human-readable, harder to diff/review
3. **Hermes memory tool** — limited to 2KB, not suitable for product docs
4. **Separate Obsidian vault** — essentially the same as this approach but isolated; the `docs/` folder serves the same purpose
