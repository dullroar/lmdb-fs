---
gist: "Read when: renaming the project or package, or explaining where the idea came from (ScienceXchange, earlier LDAP work)."
---

# Name and lineage

**Decision.** The project is `lmdb-fs`, naming the prototype that exists (LMDB indexes exposed through a filesystem interface) and keeping its lineage honest. The distribution and command are `lmdb-fs`; the Python package is `lmdb_fs`.

**Lineage.** The idea arose from ScienceXchange (finding the right experimental dataset when the useful starting dimension cannot be predicted) and an earlier exploration of LDAP, where the hierarchy is mostly a naming structure and the useful operation is intersection over attributes. A recorded 2001 experience (more than 8,000 random network searches/retrievals per second against a roughly 600 MB directory on modest hardware) shows workload fit for indexed attribute reads over largely immutable records; that implementation is not recreated here.
