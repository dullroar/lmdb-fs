---
gist: "Read when: changing the repository's design, boundaries or dependencies, or before simplifying a deliberate seam."
---

# Architecture premises

One durable design decision per file: the constraint, the choice, why, and what would contradict it. Open only the premise whose **Read when** line matches the task.

<!-- BEGIN GENERATED CONTEXT INDEX -->

* [filesystem-as-universal-ui.md](./filesystem-as-universal-ui.md).
  Read when: questioning why discovery is a filesystem rather than a search page or SDK, or designing how a faceted query is exposed.
* [lmdb-first-backend.md](./lmdb-first-backend.md).
  Read when: changing the index structure, the MetadataBackend boundary, intersection strategy, or planning an OpenLDAP or other backend comparison.
* [naming-and-lineage.md](./naming-and-lineage.md).
  Read when: renaming the project or package, or explaining where the idea came from (ScienceXchange, earlier LDAP work).
* [path-is-accumulated-predicate.md](./path-is-accumulated-predicate.md).
  Read when: changing how paths map to queries, facet and child-directory rules, path encoding, or the files shown at a query directory.
* [read-only-immutable-corpus.md](./read-only-immutable-corpus.md).
  Read when: asked to add create, rename, write or metadata-editing behavior, or to support a mutable collection.

<!-- END GENERATED CONTEXT INDEX -->
