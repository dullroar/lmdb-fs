---
gist: "Read when: a broad mounted directory is slow, or changing directory-listing materialization, paging or snapshot behavior."
---

# Broad directory listings measure materialization, not intersection

- 2026-09-20 - A broad mounted-directory `readdir` measures result materialization, not LMDB intersection performance: 131,782 entries took about 4.83 seconds. Snapshot directory entries once per open handle; recalculating a million-entry listing for each paged callback is pathological. See `docs/benchmark-results.md` for the measured runs.
