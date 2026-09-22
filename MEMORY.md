# MEMORY.md

Non-obvious findings about this codebase and its operating environment, discovered during work but not designed for anywhere else — not in README.md (what it is and how to use it), DESIGN.md (architectural decisions), or agent-instruction files (rules). This is background context for whichever LLM works in this repository next, so it does not have to rediscover these findings the hard way.

If you (an LLM) make a finding like the ones below — a gotcha, an environment quirk, or a non-obvious reason one component reads or uses another — add it here rather than only mentioning it in chat. Keep entries factual and dated; note when something might have been fixed since.

## Findings

- 2026-09-20 — In this WSL environment, FUSE was initially unavailable: /dev/fuse was absent and pyfuse3 could not build. Before diagnosing application code, confirm that FUSE is enabled, libfuse3-dev and pkg-config are installed, and /dev/fuse is character device 10:229. Recheck on a new host.
- 2026-09-20 — A broad mounted-directory readdir measures result materialization, not LMDB intersection performance: 131,782 entries took about 4.83 seconds. Snapshot directory entries once per open handle; recalculating a million-entry listing for each paged callback is pathological.
