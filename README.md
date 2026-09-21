# lmdb-fs / SemanticFS

`lmdb-fs` is a read-only FUSE filesystem whose directories are faceted metadata
queries and whose files are immutable payloads. A path such as
`/year=2026/disease=COVID/` means `year=2026 AND disease=COVID`; it is not a
physical directory hierarchy.

The public Python package and command are named `semanticfs` because they
describe the filesystem abstraction rather than its first storage backend.

## Status

This is a greenfield prototype. The first required milestone is a verified
pyfuse3 mount on the target WSL environment; the semantic model and LMDB index
follow once that platform gate passes.

## Target environment observed on 2026-09-20

- Ubuntu 24.04.4 under WSL2, kernel `6.6.87.2-microsoft-standard-WSL2`
- Python 3.12.3
- FUSE 3.14.0 (`fuse3`, `libfuse3-dev`, `pkg-config`)
- pyfuse3 3.5.0 and lmdb 2.3.0, managed by `uv`

The WSL FUSE device was not created automatically after loading the built-in
module. If `/dev/fuse` is absent, an administrator must run:

```bash
sudo modprobe fuse
sudo mknod -m 666 /dev/fuse c 10 229
```

This only prepares the device; normal filesystem mounts are performed as the
ordinary user. The smoke command is:

```bash
uv run python tools/fuse_smoke.py /tmp/semanticfs-smoke
```

Use `fusermount3 -u /tmp/semanticfs-smoke` to unmount after testing.

## Development

```bash
uv sync --all-groups
uv run pytest
```

Generated payloads and LMDB environments belong under `data/` and are ignored
by Git.
