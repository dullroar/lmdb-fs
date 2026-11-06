# lmdb-fs First-Pass Prototype Plan

## 0. Mission

Build a working, read-only **faceted semantic filesystem** on Terra
under WSL/Linux.

The filesystem is a user interface over immutable scientific-style data
objects and their metadata. It should let any filesystem-aware tool
navigate a metadata query as if it were a directory tree, without
requiring the tool to understand the metadata store or query language.

The core idea is:

> A path is not physical containment. A path is an accumulated set of
> metadata predicates.

For example:

    /year=2026/disease=COVID/lab=LANL/

means:

    year = 2026
    AND disease = COVID
    AND lab = LANL

At every directory, lmdb-fs presents:

1.  the data nodes/files satisfying all predicates accumulated so far;
    and
2.  subdirectories representing **remaining, unused facet/value
    predicates** that can further describe/filter the current result
    set.

A facet may occur at most once in a path. Thus, after entering
`year=2026`, no `year=*` directory may appear below that point. This
makes the apparent tree finite: maximum predicate depth is bounded by
the number of defined facets.

This is a prototype intended to answer two questions:

1.  Is "filesystem as universal faceted-search UI" still a useful
    interaction model?
2.  Can it be **FAST FAST** on modern commodity hardware when backed by
    an index optimized for read-heavy set intersection?

Do not over-engineer the first pass. Produce a small, comprehensible
system that can be benchmarked, abused from normal Unix tools, and
extended later.

------------------------------------------------------------------------

## 1. First-Pass Design Decisions

Use these as defaults unless investigation during implementation finds a
concrete blocker.

### Platform

-   Terra
-   WSL2
-   Ubuntu/Linux user space
-   Python 3.12+ if readily available
-   FUSE 3
-   `pyfuse3` as the initial Python FUSE binding
-   LMDB as the initial metadata/index backend
-   immutable local files as the initial data-object payloads

Before coding, verify that the installed WSL kernel and environment
support FUSE mounts and that `pyfuse3` installs cleanly. Record actual
versions in the README.

### Read-only semantics

lmdb-fs is deliberately read-only.

The following should work:

-   `ls`
-   `find`
-   `stat`
-   `cat`
-   `head`
-   `grep`
-   Python `open()`
-   normal applications opening a file through the mount
-   directory traversal from shells and filesystem APIs

Mutation operations are outside the problem space and should fail
cleanly with `EROFS`, including:

-   create
-   mkdir
-   unlink
-   rmdir
-   rename/mv
-   write/truncate
-   symlink creation
-   metadata mutation

Do not spend first-pass effort inventing write semantics.

### Backend

Start with **LMDB directly**, not OpenLDAP.

The purpose of this choice is to test the filesystem/query idea with a
minimal, very fast local backend. Keep the storage/query interface clean
enough that OpenLDAP can later be implemented as a second backend for a
historically interesting and architecturally useful comparison.

Do not tightly couple FUSE operations to LMDB calls.

------------------------------------------------------------------------

## 2. Semantic Model

### 2.1 Data node

A data node represents one immutable dataset/file.

Each node has at minimum:

    node_id
    display_name
    payload_path
    metadata

Example:

    node_id: 18427
    display_name: experiment-18427.csv
    payload_path: /path/to/lmdb-fs-data/payloads/experiment-18427.csv
    metadata:
        year: 2026
        disease: COVID
        lab: LANL
        species: mouse
        assay: PCR

`node_id` must be stable and independent of the virtual path used to
discover the node.

A single node may therefore be visible through many virtual paths.

### 2.2 Facet

A facet is a metadata dimension that may become a directory predicate.

Initial synthetic schema should use approximately 12--16 facets, for
example:

-   year
-   institution
-   lab
-   project
-   investigator
-   disease
-   species
-   tissue
-   assay
-   instrument
-   protocol
-   funding_source
-   geography
-   sample_type
-   study_phase

Use values with deliberately different cardinalities. `year` may have
only 20 values while `investigator` may have tens of thousands.

This matters for realistic indexing and benchmark behavior.

### 2.3 Path predicate

Each virtual directory component has the form:

    facet=value

Example:

    /year=2026/disease=COVID/species=mouse/

Parse this into an unordered predicate set:

    {
        ("year", "2026"),
        ("disease", "COVID"),
        ("species", "mouse")
    }

Order in the visible path is meaningful only as the user's navigation
history. It must not change the query result.

Therefore:

    /year=2026/disease=COVID/

and:

    /disease=COVID/year=2026/

must identify equivalent result sets.

### 2.4 Canonical query key

Canonicalize every parsed predicate set before querying or caching.

For example:

    canonical_key = tuple(sorted([
        ("year", "2026"),
        ("disease", "COVID")
    ]))

Both path permutations above must generate the same canonical key.

Use this canonical form for:

-   query-result caching
-   directory-content caching
-   tests of path-order equivalence
-   logging
-   performance metrics

Do **not** rewrite the user's visible path to canonical order.
Canonicalization is internal.

### 2.5 No repeated facets

A valid path may contain a facet at most once.

If `year=2026` is already present, no `year=*` directories may be
emitted below that path.

If a caller manually attempts a path such as:

    /year=2026/disease=COVID/year=2025/

return an appropriate not-found/invalid-path result rather than treating
it as a valid query.

This invariant prevents recursive facet loops and bounds maximum
predicate depth by the number of facets.

### 2.6 Directory contents

For a current predicate set `P`, a directory contains:

1.  all data nodes satisfying `P`; and
2.  facet/value subdirectories for unused facets whose values occur
    among nodes satisfying `P`.

For:

    /year=2026/disease=COVID/

the result might resemble:

    assay=ELISA/
    assay=PCR/
    lab=LANL/
    lab=Sandia/
    species=human/
    species=mouse/
    experiment-00417.csv
    experiment-01932.csv
    experiment-08722.json

Never emit a facet/value directory whose intersection with the current
result set is empty.

### 2.7 Redundant facets

For the first pass, **show** a valid remaining facet/value even when
selecting it would not reduce the result set.

Example: if every current result has `species=mouse`, still show:

    species=mouse/

This exposes useful information about the result set and keeps the rule
simple.

However, design this as a policy so a later mount/config option can
implement:

    hide_redundant_facets = true

Under that policy, a child facet/value is emitted only if it strictly
reduces the result set.

Do not implement this option until the basic filesystem works unless it
is trivial.

### 2.8 Files at every level

Matching files should be visible at every query directory, not only at
terminal leaves.

Thus:

    /year=2026/

contains the files satisfying `year=2026` plus available facet
directories.

And:

    /year=2026/disease=COVID/

contains the narrower matching files plus remaining facets.

This is intentional. The user can stop filtering whenever the result set
is useful.

For very large result sets, directory enumeration itself may become
unwieldy. Do not hide this problem. Measure it. A later version may need
paging, threshold policies, special result directories, or other
strategies, but first establish actual behavior.

------------------------------------------------------------------------

## 3. Architecture

Keep four conceptual layers separate.

    +----------------------------------+
    | Linux apps / shell / File Open   |
    +----------------+-----------------+
                     |
                     | POSIX/VFS calls
                     v
    +----------------------------------+
    | FUSE adapter                     |
    | pyfuse3 operations               |
    +----------------+-----------------+
                     |
                     | semantic requests
                     v
    +----------------------------------+
    | lmdb-fs query/model layer        |
    | path parsing                     |
    | canonicalization                 |
    | facet rules                      |
    | directory construction           |
    +----------------+-----------------+
                     |
                     | backend interface
                     v
    +----------------------------------+
    | LMDB index backend               |
    | inverted indexes                 |
    | node metadata                    |
    +----------------+-----------------+
                     |
                     | node -> payload
                     v
    +----------------------------------+
    | immutable local payload files    |
    +----------------------------------+

The FUSE layer should know as little as possible about LMDB.

The query/model layer should be testable without mounting a filesystem.

------------------------------------------------------------------------

## 4. Repository Layout

Use something close to:

    lmdb-fs/
        README.md
        plan.md
        pyproject.toml
        .gitignore

        src/
            lmdb_fs/
                __init__.py
                cli.py
                config.py
                model.py
                paths.py
                query.py
                cache.py

                backends/
                    __init__.py
                    base.py
                    lmdb_backend.py

                fuse/
                    __init__.py
                    operations.py
                    inode_table.py

        tools/
            generate_data.py
            build_index.py
            benchmark_queries.py
            benchmark_fs.py

        tests/
            test_paths.py
            test_query.py
            test_lmdb_backend.py
            test_invariants.py
            test_fuse_integration.py

        data/
            .gitkeep

        docs/
            architecture.md
            benchmark-results.md

Do not commit generated multi-gigabyte benchmark datasets or LMDB
environments.

------------------------------------------------------------------------

## 5. Backend Interface

Define a small abstract/protocol interface before implementing LMDB.

Something approximately like:

    class MetadataBackend(Protocol):
        def all_node_ids(self) -> NodeSet: ...
        def match(self, predicates: PredicateSet) -> NodeSet: ...
        def remaining_facets(
            self,
            predicates: PredicateSet,
            matched_nodes: NodeSet,
        ) -> Mapping[str, Mapping[str, int]]: ...
        def get_node(self, node_id: int) -> Node: ...
        def get_nodes(self, node_ids: Iterable[int]) -> Iterable[Node]: ...

Do not treat this exact signature as sacred. Optimize it after profiling
if necessary.

The important point is that a future:

    OpenLDAPBackend

should be possible without rewriting FUSE.

------------------------------------------------------------------------

## 6. LMDB Index Design

The dominant operation is set intersection.

Do not begin with "store JSON records and scan them."

Build an inverted index.

Conceptually:

    ("year", "2026")       -> node ID set
    ("disease", "COVID")   -> node ID set
    ("lab", "LANL")        -> node ID set

Then:

    match({
        year=2026,
        disease=COVID,
        lab=LANL
    })

is:

    nodes(year=2026)
        INTERSECT nodes(disease=COVID)
        INTERSECT nodes(lab=LANL)

Start intersection with the smallest posting list.

### Node-set representation

This is an explicit experiment point.

First implement the simplest representation that is fast enough to build
and verify. Candidate approaches include:

-   sorted integer arrays
-   compact packed integer lists
-   roaring bitmaps if a mature Python-accessible implementation
    integrates cleanly
-   bitsets for dense synthetic IDs

Do not introduce a complex dependency without measuring its benefit.

Design the backend so the posting-list representation can change without
affecting the semantic layer.

### LMDB logical databases

Consider separate named LMDB databases for:

    nodes
    facet_postings
    facet_values
    metadata

Possible key forms:

    node:<id>
    facet:<facet>:<value>

Use binary-safe, deterministic encoding.

Avoid clever serialization initially. Prefer something easy to inspect
and benchmark.

### Read transactions

Exploit LMDB's read-heavy strengths:

-   reuse the environment
-   use short-lived or safely managed read transactions
-   avoid unnecessary copying
-   do not add an application cache merely because caches seem
    fashionable

Measure before adding layers.

------------------------------------------------------------------------

## 7. Synthetic Data Generator

The benchmark corpus is part of the product, not an afterthought.

Create deterministic synthetic data using a fixed seed.

Support at least:

    --nodes 10000
    --nodes 100000
    --nodes 1000000
    --nodes 10000000

Do not require creation of 10 million large payload files.

For large benchmarks, payloads may be tiny placeholders or a smaller
reusable payload corpus while metadata contains millions of logical
nodes. Clearly distinguish metadata-query benchmarks from actual
file-open benchmarks.

Generate distributions that are not uniformly random.

Examples:

-   years: low cardinality
-   disease: medium cardinality with skew
-   lab: hundreds/thousands
-   investigator: high cardinality
-   instrument: medium cardinality
-   assay: low/medium cardinality
-   geography: hierarchical-looking values but treated as ordinary
    facets
-   species: low cardinality
-   project: high cardinality

Include correlations:

-   some labs specialize in certain assays
-   some diseases correlate with species
-   investigators cluster by institution
-   instruments cluster by lab

This makes facet elimination realistic and prevents every query from
behaving like independent random data.

Emit a manifest describing the generated corpus and seed.

------------------------------------------------------------------------

## 8. FUSE Implementation

Implement the minimum useful FUSE surface.

Prioritize:

-   lookup
-   getattr
-   opendir
-   readdir
-   open
-   read
-   release, if required by binding/lifecycle
-   statfs, minimally

Mutating operations should return `EROFS` where applicable.

### Virtual directories

A virtual directory corresponds to a predicate set.

It does not need a persistent backing directory.

Directory identity should be deterministic enough for a mounted session.

### Inodes

Create an inode-management strategy for:

-   virtual query directories
-   virtual file appearances
-   underlying data nodes

Remember that the same underlying data node may appear under many
virtual directories.

For the first pass, correctness and stable behavior within a mount
matter more than inventing a globally permanent inode scheme.

Document the choice.

### File reads

When a matching virtual file is opened, map its node ID to the immutable
payload path and service reads from that payload.

Avoid copying the payload into the metadata database.

### Filenames

Use a deterministic display filename.

Handle collisions explicitly. Two nodes may have the same original
filename.

A safe first-pass convention could be:

    <node_id>--<original_name>

or another reversible scheme.

Do not silently drop one colliding node.

### Escaping facet values

Facet values may contain:

-   `/`
-   `=`
-   spaces
-   Unicode
-   shell-significant characters

Define a reversible pathname encoding.

Do not postpone this until after the happy-path implementation, because
ambiguous path parsing will contaminate everything above it.

Prefer human-readable escaping where practical.

Add round-trip tests.

------------------------------------------------------------------------

## 9. Caching

Implement correctness without caching first.

Then profile.

Likely cache targets:

1.  canonical predicate set -\> matching node set
2.  canonical predicate set -\> generated child facet/value entries
3.  parsed virtual path -\> canonical predicate set

Use bounded caches.

Instrument cache hits/misses.

Because different path orders canonicalize to the same predicate set:

    /year=2026/disease=COVID/

and:

    /disease=COVID/year=2026/

must share query-cache entries.

This is an important architectural benefit and an explicit test.

------------------------------------------------------------------------

## 10. Correctness Invariants

Automate these.

### Invariant 1: facet uniqueness

No valid emitted path contains the same facet twice.

### Invariant 2: finite depth

Maximum predicate depth is no greater than the number of configured
facets.

### Invariant 3: monotonic filtering

For parent predicate set `P` and child `P + q`:

    match(P + q) SUBSET-OF match(P)

Always.

### Invariant 4: nonempty emitted child

Every emitted facet/value directory has at least one matching node.

### Invariant 5: path-order equivalence

All permutations of the same predicate set produce identical matching
node IDs.

For a manageable predicate count, use property-based tests to generate
permutations.

### Invariant 6: file correctness

Every file emitted in a directory satisfies every predicate represented
in that directory path.

### Invariant 7: completeness

Every indexed node satisfying the current predicates appears in the
directory result unless an explicitly documented enumeration policy says
otherwise.

First pass should aim for complete enumeration.

### Invariant 8: read-only behavior

Mutation attempts fail and do not alter backend or payload data.

### Invariant 9: escaping round trip

Every legal metadata value used as a directory component can be encoded
and decoded without information loss.

------------------------------------------------------------------------

## 11. Development Milestones

Work in small checkpoints. Commit after each stable milestone.

### Milestone 1 --- Environment proof

Goal: prove FUSE works on Terra/WSL.

Tasks:

-   inspect WSL/Linux/Python/FUSE versions
-   install minimal dependencies
-   mount a tiny pyfuse3 hello-world filesystem
-   verify `ls`, `stat`, and `cat`
-   unmount cleanly
-   document exact setup commands

Commit:

    chore: prove pyfuse3 filesystem on WSL

Do not proceed until this works reliably.

### Milestone 2 --- Pure semantic model

No FUSE yet.

Implement:

-   facet/value path encoding
-   path parsing
-   duplicate-facet rejection
-   predicate canonicalization
-   in-memory toy backend
-   directory-content generation

Use perhaps 20 hand-authored experiment nodes.

Tests should demonstrate:

    /year=2026/disease=COVID/

and:

    /disease=COVID/year=2026/

return the same files and logically equivalent child choices.

Commit:

    feat: implement faceted path and query semantics

### Milestone 3 --- LMDB backend

Implement:

-   index builder
-   node storage
-   facet/value posting lists
-   set intersection
-   remaining-facet discovery

Run semantic tests against both:

-   in-memory backend
-   LMDB backend

They must produce equivalent results.

Commit:

    feat: add LMDB metadata backend

### Milestone 4 --- Mount semantic model through FUSE

Wire the tested semantic layer into pyfuse3.

Verify manually:

    ls /mnt/lmdb-fs
    ls /mnt/lmdb-fs/year=2026
    ls /mnt/lmdb-fs/year=2026/disease=COVID

Then reverse traversal order:

    ls /mnt/lmdb-fs/disease=COVID/year=2026

Verify matching files are identical.

Verify used facets disappear from child choices.

Commit:

    feat: expose faceted queries through FUSE

### Milestone 5 --- Real payload reads

Add immutable payload files and verify:

    cat
    head
    grep
    cp FROM lmdb-fs
    python open()

Work through the mounted filesystem.

Attempt writes and verify `EROFS`.

Commit:

    feat: support read-only payload access

### Milestone 6 --- Synthetic scale generator

Generate deterministic corpora at:

-   10K
-   100K
-   1M

Attempt 10M only after measuring resource use at 1M.

Record:

-   generation time
-   index-build time
-   LMDB size
-   process memory
-   query latency

Commit:

    feat: add scalable synthetic experiment corpus

### Milestone 7 --- Benchmark harness

Benchmark both the semantic query layer and mounted filesystem.

Commit:

    perf: add query and filesystem benchmarks

### Milestone 8 --- Profile and optimize

Only now optimize.

Find actual hotspots.

Candidates may include:

-   posting-list intersection
-   repeated remaining-facet calculations
-   Python object allocation
-   serialization/deserialization
-   inode lookup
-   FUSE call volume
-   huge `readdir` results

Make each meaningful optimization measurable and commit separately where
practical.

Do not "optimize" by intuition alone.

------------------------------------------------------------------------

## 12. Benchmark Plan

The emotional target is:

> "No, that cannot be right. Prove the benchmark isn't broken."

But report measurements honestly.

### Query-layer benchmark

Measure without FUSE so kernel/userspace overhead is separable from
index performance.

Test:

-   one predicate
-   two predicates
-   three predicates
-   five predicates
-   high-cardinality predicates
-   low-cardinality predicates
-   common values
-   rare values
-   zero-result queries

Record at least:

-   median latency
-   p95
-   p99
-   queries/sec
-   result-set size
-   warm vs cold-ish behavior where practical

### Directory benchmark

Measure:

    ls <mount>/year=2026

and progressively selective paths.

Separate:

-   time to determine matching node set
-   time to calculate child facets
-   time to enumerate matching files
-   total `readdir` time

Large result enumeration may dominate even if the index query is nearly
instantaneous. That is useful information.

### Path-order/cache benchmark

Repeatedly query permutations of the same predicates.

Confirm canonicalization causes cache reuse.

### Parallel benchmark

Use multiple processes or threads performing independent directory walks
and file opens.

Test representative concurrency such as:

-   1 client
-   4 clients
-   16 clients
-   32 clients

Do not chase arbitrary benchmark numbers before establishing correct
behavior.

### Corpus sizes

Aim for:

    10K -> correctness/smoke
    100K -> routine development
    1M -> meaningful benchmark
    10M -> stretch benchmark

If 10M is easy, increase it.

The purpose is to find where the architecture bends.

### Comparison baseline

Include at least one deliberately simple baseline, such as a Python scan
over metadata, so the indexed design has a sanity comparison.

Later, not first pass, compare LMDB against OpenLDAP using the same
logical corpus and query workload.

------------------------------------------------------------------------

## 13. Observability

Add lightweight structured logging.

Useful events:

-   mount/unmount
-   parsed path
-   canonical predicate key
-   backend query latency
-   matched-node count
-   remaining-facet calculation latency
-   generated directory-entry count
-   cache hit/miss
-   payload open/read errors

Do not log every file read at INFO during benchmarks.

Support a quiet benchmark mode.

Expose timing counters in a way benchmark scripts can collect without
parsing decorative human logs if practical.

------------------------------------------------------------------------

## 14. CLI

Aim for a small CLI such as:

    lmdb-fs build-index \
        --metadata data/experiments.jsonl \
        --db data/index.lmdb

    lmdb-fs mount \
        --db data/index.lmdb \
        --mountpoint /mnt/lmdb-fs

    lmdb-fs unmount \
        --mountpoint /mnt/lmdb-fs

Exact syntax may change.

Useful development options:

    --debug
    --foreground
    --no-cache
    --cache-size N

Keep configuration boring.

------------------------------------------------------------------------

## 15. WSL Setup and Operational Notes

Codex should determine and document the exact current commands rather
than blindly assuming package names.

Likely requirements include:

-   FUSE 3 runtime/development packages
-   Python development tooling
-   `pyfuse3`
-   LMDB Python binding
-   pytest
-   optional property-based testing package such as Hypothesis
-   benchmark tooling

Check:

    uname -a
    python3 --version
    fusermount3 --version

Confirm `/dev/fuse` exists and a non-root user can mount a FUSE
filesystem.

Prefer user mounts. Do not make the prototype require root during normal
operation.

Provide a clean unmount path and document recovery from a crashed
userspace filesystem process.

------------------------------------------------------------------------

## 16. Tests Beyond Unit Tests

Once mounted, create a shell-level smoke test.

Examples:

    test -d /mnt/lmdb-fs/year=2026

    find /mnt/lmdb-fs/year=2026/disease=COVID \
        -maxdepth 1 \
        -type f

Use ordinary filesystem tools deliberately. The entire point is that
they should work without lmdb-fs-aware clients.

Also test from Python using ordinary `pathlib` and `open()`.

If practical, test opening a payload through VS Code or another ordinary
application via the mounted path. This is a qualitative proof of the
"filesystem as UI" premise.

------------------------------------------------------------------------

## 17. Explicit Non-Goals for First Pass

Do not implement:

-   write support
-   metadata editing
-   distributed operation
-   network filesystem serving
-   cloud blob storage
-   authentication/authorization
-   ACL projection
-   LDAP backend
-   web UI
-   REST API
-   GraphQL
-   natural-language search
-   vector search
-   ontology inference
-   automatic metadata extraction
-   production crash recovery guarantees
-   Windows-native filesystem projection
-   fancy result-count pseudo-files
-   cross-machine synchronization

Do not let interesting adjacent ideas prevent a mountable prototype from
existing.

------------------------------------------------------------------------

## 18. Questions the Prototype Should Answer

At the end of the first pass, write `docs/benchmark-results.md` and
answer:

1.  Does faceted traversal feel natural from a shell?
2.  Is seeing matching files at every level useful or overwhelming?
3.  Does suppressing already-used facets adequately prevent
    directory-maze behavior?
4.  At what result-set size does normal directory enumeration become
    unpleasant?
5.  Is maximum depth naturally bounded and understandable?
6.  Do alternate facet orders feel useful or merely redundant?
7.  How much benefit does canonical query caching provide?
8.  Is LMDB query time material compared with
    FUSE/Python/directory-enumeration overhead?
9.  What operation is actually the bottleneck at 1M and 10M nodes?
10. Does the filesystem abstraction make ordinary tools unexpectedly
    useful?
11. Are there POSIX assumptions from ordinary applications that expose
    flaws in the model?
12. Does this still feel like a useful architecture after actually
    living in it?

The last question matters as much as the benchmark.

------------------------------------------------------------------------

## 19. Second-Pass Experiments --- Do Not Implement Yet

Capture these as issues/TODOs after the first pass.

### OpenLDAP backend

Implement the same backend interface over OpenLDAP.

Load equivalent synthetic metadata.

Compare:

-   index-build/load time
-   single-query latency
-   concurrent-query throughput
-   remaining-facet discovery cost
-   memory
-   disk
-   operational complexity

This is the direct descendant of the original ScienceXchange experiment.

### Hide redundant facets

Mount/config option:

    show_redundant_facets = true|false

Test whether strict selectivity makes navigation better.

### Result-count metadata

Explore exposing counts without making pathnames unstable.

Possible mechanisms:

-   extended attributes
-   special metadata pseudo-files
-   optional decorated display mode

### Alternate posting structures

Benchmark:

-   sorted integer arrays
-   roaring bitmaps
-   dense bitsets where appropriate

### Object/blob backend

Replace local payload paths with object storage while preserving the
filesystem/query model.

### Windows-facing access

Only after Linux/WSL semantics are proven, investigate whether the same
semantic layer could be exposed through a Windows filesystem mechanism
or network filesystem without compromising the clean model.

------------------------------------------------------------------------

## 20. Coding-Agent Working Rules

Codex should treat this as an exploratory systems prototype, not a
feature checklist.

### Before making a major design change

State:

1.  what problem was observed;
2.  why the current design fails or is materially awkward;
3.  the smallest change that addresses it;
4.  how the change will be tested or benchmarked.

### Prefer empirical decisions

If choosing between two representations because one is supposedly
faster, benchmark them.

If FUSE appears slow, profile before blaming FUSE.

If LMDB appears magical, verify query correctness before celebrating.

We have historical precedent for this requirement.

### Keep the layers separable

Do not allow:

    pyfuse3 callback -> random LMDB implementation details

to spread through the codebase.

The semantic query engine should remain independently testable.

### Keep dependencies modest

This prototype is specifically interested in leverage from existing
universal interfaces. Do not bury it under a framework stack.

### Preserve comprehensibility

A competent engineer should be able to read the core path/query logic in
one sitting.

This is an experiment in an idea, not an enterprise platform.

------------------------------------------------------------------------

## 21. Definition of Done for First Pass

The first pass is done when all of the following are true:

-   lmdb-fs mounts successfully in WSL as an ordinary user.
-   A deterministic synthetic corpus of at least 1 million metadata
    nodes can be indexed.
-   A user can navigate metadata facets with ordinary `cd`/`ls`.
-   Used facets never reappear beneath the current path.
-   Matching files appear at every query level.
-   Different facet orders produce identical result sets.
-   Normal tools can open/read matching payload files.
-   Mutation attempts fail read-only.
-   Automated invariant tests pass.
-   Query and filesystem benchmark harnesses exist.
-   Results for at least 10K, 100K, and 1M nodes are recorded.
-   A 10M-node run has either been completed or its limiting
    resource/bottleneck has been identified.
-   The actual bottlenecks have been profiled.
-   README contains reproducible setup/build/mount/test/benchmark
    instructions.
-   `docs/benchmark-results.md` records both quantitative results and
    qualitative observations about using the filesystem.

At that point, stop.

Review what was learned before adding LDAP, object storage, a Windows
projection, or any other second-generation machinery.

------------------------------------------------------------------------

## 22. North Star

Do not lose the original idea while implementing machinery:

> **The filesystem is the UI.**

The metadata engine answers set-membership questions.

FUSE turns those answers into directories and files.

Everything else should remain blissfully unaware that it is navigating a
faceted query engine.
