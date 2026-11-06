---
gist: "Read when: asked to add create, rename, write or metadata-editing behavior, or to support a mutable collection."
---

# Read-only over an immutable corpus

**Decision.** The corpus is immutable after ingest; payloads and metadata are a read-only source of truth. All mutations return `EROFS`.

**Why.** The constraint is architectural, not incidental: it removes the hard and misleading half of POSIX emulation (create, move, rename, conflict handling, metadata editing). The useful surface is `lookup`, `readdir`, `stat`, `open` and `read`.

**Contradicted by.** A requirement for a writable object store, cloud filesystem, access control, web catalog, or general POSIX replacement. These are non-goals.
