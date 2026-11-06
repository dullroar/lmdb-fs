---
gist: "Read when: changing the index structure, the MetadataBackend boundary, intersection strategy, or planning an OpenLDAP or other backend comparison."
---

# LMDB first, behind a backend protocol

**Decision.** Start with LMDB (`FUSE -> Python -> LMDB -> immutable payloads`) rather than LDAP (`FUSE -> Python -> LDAP -> directory server -> LMDB`). OpenLDAP's `mdb` backend itself uses LMDB, and the shortcut avoids LDAP protocol, a server process and query-planner behavior.

**Index.** Inverted: a `(facet, value)` key maps to a duplicate-sorted set of node IDs; a query intersects sets, beginning with the smallest posting and probing the rest, so selective queries do not allocate broad lists.

**Boundary.** The backend protocol is deliberately separate from FUSE so an OpenLDAP backend can later be compared on the same corpus and benchmark harness. The stable idea is set-oriented discovery through a universal interface; LMDB is the minimal first vehicle.
