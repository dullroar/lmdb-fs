# Project Memory

> Version-controlled, cross-LLM continuity notes. Keep this file compact, factual, and useful to a future contributor.

## Current context

- lmdb-fs is a read-only, faceted filesystem implemented with LMDB and pyfuse3.
- Its interface models the filesystem as a UI: paths accumulate predicates over immutable, scientific-style data.

## Durable implementation facts

- Facet/value postings use duplicate-sorted LMDB records. For an intersection, count postings, enumerate the smallest list, and probe the others.
- Facets already used in a path disappear from the next directory level. This prevents repeated-facet loops and bounds traversal depth.
- Broad directory listing is result materialization, not an index-intersection benchmark. Snapshot entries once per open handle rather than recomputing a large listing for each paged callback.
- Bound cached results with cache_max_nodes=10_000. Use --no-cache or --cache-size 0 for comparison runs.
- Final public identifiers are Python package lmdb_fs, executable lmdb-fs, and console script lmdb-fs = "lmdb_fs.cli:main".
- DESIGN.md documents the current LMDB implementation and the LDAP/ScienceXchange lineage.

## Verified workflow

- 2026-09-20: uv sync --locked --all-groups, uv run pytest -q, the opt-in FUSE integration test, and uv run lmdb-fs --help all passed. The regular suite reported 29 passes with one non-opt-in integration test skipped.

## Decisions

- Preserve read-only semantics and ordinary filesystem-tool access; do not broaden the project into a general writable filesystem.

## Open questions

- None recorded.
