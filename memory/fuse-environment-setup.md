---
gist: "Read when: mounting fails, /dev/fuse is missing, or pyfuse3 will not build, especially on a new host or in WSL."
---

# FUSE availability in WSL

- 2026-09-20 - In this WSL environment FUSE was initially unavailable: `/dev/fuse` was absent and pyfuse3 could not build. Before diagnosing application code, confirm FUSE is enabled, `libfuse3-dev` and `pkg-config` are installed, and `/dev/fuse` is character device 10:229. Recheck on a new host.
