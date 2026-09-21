# lmdb-fs design lineage

## Purpose and name

`lmdb-fs` is a read-only FUSE projection over immutable, metadata-rich data
objects. A directory path is an accumulated metadata predicate, not physical
containment:

```text
/year=2026/disease=COVID/lab=LANL/
```

means:

```text
year = 2026 AND disease = COVID AND lab = LANL
```

The project is named `lmdb-fs` rather than a generic semantic-filesystem label
for two reasons:

1. It names the prototype that actually exists: LMDB indexes exposed through a
   filesystem interface.
2. It retains the historical lineage honestly. The central idea predates this
   implementation; it arose from ScienceXchange and an earlier exploration of
   LDAP as a high-performance, attribute-oriented data-discovery system.

The distribution and command use `lmdb-fs`. The Python package is `lmdb_fs`,
the conventional underscore spelling required by Python imports.

## Historical origin

The original problem was ScienceXchange: how should a future researcher find
the right experimental dataset when the useful starting dimension cannot be
predicted in advance? The intended corpus was immutable after ingest. Payloads
and metadata were therefore a read-only source of truth for an experiment, not
a collaborative mutable filesystem.

That constraint is architectural, not incidental. It removes the hard and
misleading half of POSIX emulation: no create, move, rename, conflict handling,
or metadata editing semantics need be invented for a dynamic query projection.
The useful surface is enumeration and access: `lookup`, `readdir`, `stat`,
`open`, and `read`.

The preceding LDAP work supplied the conceptual model. Its important lesson
was that LDAP's apparent hierarchy is primarily a naming structure; its useful
expressive operation is intersection over attributes. In the shorthand from
that work: do not think navigation or underlying organization—think sets,
set theory, and Venn diagrams.

The recorded 2001 experience also supplied an empirical reason to take the
idea seriously: more than 8,000 random network searches/retrievals per second
against a roughly 600 MB directory, on an 800 MHz machine with 512 MB RAM.
The exact historical implementation is not recreated here. The point is the
workload fit: many indexed, attribute-based reads over largely immutable
records can be astonishingly fast when the storage model is built for it.

## Filesystem as a universal UI

The filesystem is not being mistaken for a disk format. It is being used as a
widely implemented protocol for named things:

```text
enumerate, open, read, seek, stat
```

Ordinary programs already speak that protocol. A faceted query represented as
a path becomes an addressable computational object: it can be passed to `ls`,
`find`, `grep`, Python, an editor, a script, or another old application without
a catalog-specific SDK. `/proc` is the familiar proof that a useful filesystem
projection need not correspond to stored files.

For this workload, a path is progressive set intersection. The query state is
portable and composable in a way a web catalog's checkbox state usually is not.

## Core invariants

- Every matching data object is visible as a file at every query directory.
- Child directories represent unused facet/value predicates that occur among
  the current matches; no empty child is emitted.
- A facet may appear at most once in a path. Used facets are absent below that
  point, bounding depth by the configured facet count and preventing loops.
- Predicate order does not change the result set. Internally, predicate pairs
  are canonicalized and share cache keys; the displayed path remains the
  caller's navigation history.
- Facet values are reversibly percent-encoded, so `/`, `=`, whitespace,
  Unicode, and shell-significant characters do not make paths ambiguous.
- Payloads remain external immutable files. All mutations return `EROFS`.

The prototype currently displays a valid remaining facet even when it would
not reduce the result set. That choice makes the current result set legible.
Whether a `hide_redundant_facets` option improves navigation is a later
experiment, not a silently assumed rule.

## Why LMDB first

LDAP remains the intellectual ancestor, but it is not the first backend here.
Modern OpenLDAP itself uses LMDB for its `mdb` backend. Starting directly with
LMDB keeps the experiment focused:

```text
FUSE -> Python -> LMDB -> immutable payloads
```

instead of adding LDAP protocol, a server process, and query-planner behavior:

```text
FUSE -> Python -> LDAP -> directory server -> LMDB
```

The index is inverted. A `(facet, value)` key maps to a duplicate-sorted set of
node IDs, and a query intersects those sets. lmdb-fs begins with the smallest
posting and probes the remaining postings, avoiding allocation of broad lists
for a selective query. The backend protocol is intentionally separate from
FUSE so an OpenLDAP comparison can later be made against the same corpus and
query workload.

## What the first measurements say

The 1M-node benchmark validates two different claims.

- Selective indexed intersection is fast: a five-predicate query with six
  results measured about 657 microseconds without cache.
- Broad directories are not magically fast: a year directory with 131,782
  visible entries took about 4.83 seconds to enumerate through FUSE.

The limiting work is broad-result materialization—node decoding,
remaining-facet calculation, virtual-entry allocation, and ordinary directory
enumeration—not the selective LMDB lookup. This is a useful result, not a
failure to be hidden. It identifies the next design question: what explicit
enumeration policy, paging model, or presentation convention makes a very broad
result useful without falsifying normal filesystem semantics?

## Non-goals and next experiment

lmdb-fs is not a writable object store, cloud filesystem, access-control
system, web catalog, or generic POSIX replacement. Its first-pass job is to
test one specific proposition: can immutable scientific-style data with rich
metadata be discovered naturally through ordinary filesystem tools?

The historically appropriate second experiment is an OpenLDAP backend using
the same backend boundary, corpus, and benchmark harness. That comparison is
valuable precisely because it separates the old insight from its current
implementation: the stable idea is set-oriented discovery through a universal
interface; LMDB is the deliberately minimal first vehicle.
