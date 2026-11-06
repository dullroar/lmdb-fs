---
gist: "Read when: questioning why discovery is a filesystem rather than a search page or SDK, or designing how a faceted query is exposed."
---

# The filesystem as a universal interface

**Decision.** The filesystem is used as a widely implemented protocol for named things (enumerate, open, read, seek, stat), not as a disk format. A faceted query represented as a path becomes an addressable object usable by `ls`, `find`, `grep`, Python, editors and old applications without a catalog-specific SDK, as `/proc` shows for non-stored files.

**Why.** A path is progressive set intersection, so the query state is portable and composable in a way a web catalog's checkbox state usually is not. The model is sets and Venn diagrams, not navigation or underlying organization.
