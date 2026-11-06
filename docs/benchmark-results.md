---
gist: "Read when: judging query or directory-enumeration performance, changing caching, or comparing a backend against recorded measurements."
---

# Benchmark results

This document records measured runs, not aspirational targets. The figures
below are cache-disabled query-layer measurements (`cache_size=0`) on the
target environment: Ubuntu 24.04.4 / WSL2 kernel 6.6.87.2, Python 3.12.3,
pyfuse3 3.5.0, lmdb 2.3.0. The corpus seed was 42 and every result reports the
median of the indicated iterations.

## Method

```bash
uv run python tools/benchmark_queries.py --db /path/to/index.lmdb
uv run python tools/benchmark_fs.py /mounted/path/year=2026
```

The query harness reports canonical-query cache counters, backend match time,
remaining-facet time, and total listing-build time. The filesystem harness
reports ordinary `Path.iterdir()` latency; it intentionally includes FUSE and
kernel overhead.

## 10K

Generation was not separately timed. Index build was **0.68 s** (peak RSS
69,744 KiB); the index was **12,988,416 bytes**. Query process peak RSS was
56,000 KiB over 100 iterations per case.

| Query | Result nodes | Median |
|---|---:|---:|
| `year=2008` | 477 | 4.94 ms |
| year + disease | 168 | 1.91 ms |
| year + disease + lab | 2 | 59.3 us |
| five predicates | 1 | 48.7 us |
| high-cardinality investigator | 1 | 28.8 us |
| zero result | 0 | 5.0 us |

A deliberately simple three-predicate Python metadata scan took **56.4 ms**.

## 100K

Generation took **1.13 s**. Index build took **5.95 s** (peak RSS 241,408
KiB); the index was **168,300,544 bytes**. Query process peak RSS was 165,832
KiB over 20 iterations per case.

| Query | Result nodes | Median |
|---|---:|---:|
| `year=2008` | 5,048 | 59.4 ms |
| year + disease | 1,847 | 22.2 ms |
| year + disease + lab | 3 | 115 us |
| five predicates | 1 | 91.8 us |
| high-cardinality investigator | 1 | 30.5 us |
| zero result | 0 | 5.1 us |

## 1M

Generation took **10.90 s**. Index build took **66.99 s** (peak RSS
1,257,980 KiB); the index was **1,158,606,848 bytes**. Query process peak RSS
was 1,236,676 KiB over 5 iterations per case.

| Query | Result nodes | Median |
|---|---:|---:|
| `year=2008` | 50,049 | 840.8 ms |
| year + disease | 18,049 | 269.2 ms |
| year + disease + lab | 22 | 825.9 us |
| five predicates | 6 | 657.3 us |
| high-cardinality investigator | 11 | 149.4 us |
| zero result | 0 | 7.3 us |

The mounted filesystem benchmark used ordinary `Path.iterdir()` against this
same index. `/year=2008` had 131,782 entries (matching files plus remaining
facet values) and took **4.83 s** for one enumeration. The selective
`/year=2008/disease=COVID/lab=lab-163-00` directory had 119 entries and had a
**26.8 ms** median over three enumerations.

## What the measurements changed

The initial LMDB implementation materialized every posting list before
intersection. At 1M it made a five-predicate, six-result query take about 175
ms. The measured cause was broad posting allocation, not LMDB lookup latency.
The implementation now enumerates the smallest posting and probes the other
duplicate-sorted LMDB indexes; the equivalent post-change median is 657 us.

The current bottleneck is broad directory materialization: matching-node JSON
decode, remaining-facet discovery, virtual entry allocation, and FUSE
enumeration dominate once a query returns tens of thousands of files. A 10M
run was not attempted because this 1M measurement already identifies the
first-pass limiting behavior: root and broad directories become an unwieldy
unpaged universal listing. The next experiment should evaluate a documented
enumeration policy or paging design rather than pretending ordinary `readdir`
is an index benchmark.

## Qualitative observations

Facet paths behave naturally in ordinary shell tools: `ls`, `find`, `stat`,
`cat`, `grep`, and Python `Path.read_text()` all worked through the real FUSE
mount. Alternate facet orders produced identical files. Files at every level
are useful for selective paths, but at broad paths they make the listing itself
the UX and performance problem. Suppressing already-used facets prevents loops
and leaves a bounded maximum depth of 15 facets.
