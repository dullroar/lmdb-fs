# lmdb-fs

`lmdb-fs` is a read-only FUSE filesystem whose directories are faceted metadata
queries and whose files are immutable payloads. A path such as
`/year=2026/disease=COVID/` means `year=2026 AND disease=COVID`; it is not a
physical directory hierarchy.

The Python import package is `lmdb_fs`; the command is `lmdb-fs`. Hyphens are
valid and conventional in command names, while Python imports use underscores.
The name deliberately states the current implementation boundary: LMDB indexes
are projected through FUSE. [docs/design/](docs/design/README.md) records the older LDAP and
ScienceXchange lineage that made this design worth revisiting.

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
uv run python tools/fuse_smoke.py /tmp/lmdb-fs-smoke
```

Use `fusermount3 -u /tmp/lmdb-fs-smoke` to unmount after testing.

## Development

```bash
uv sync --all-groups
uv run pytest
```

Generated payloads and LMDB environments belong under `data/` and are ignored
by Git.

## Build and mount a corpus

```bash
uv run python tools/generate_data.py --nodes 10000 --output /tmp/lmdb-fs-corpus
uv run lmdb-fs build-index \
  --metadata /tmp/lmdb-fs-corpus/metadata.jsonl \
  --db /tmp/lmdb-fs-corpus/index.lmdb
mkdir /tmp/lmdb-fs-mount
uv run lmdb-fs mount \
  --db /tmp/lmdb-fs-corpus/index.lmdb \
  --mountpoint /tmp/lmdb-fs-mount \
  --cache-size 1024 --cache-max-nodes 10000
```

In another shell, ordinary tools can use it directly:

```bash
ls /tmp/lmdb-fs-mount/year=2026
find /tmp/lmdb-fs-mount/year=2026/disease=COVID -maxdepth 1 -type f
```

Stop the foreground mount with `Ctrl-C`, or run
`uv run lmdb-fs unmount --mountpoint /tmp/lmdb-fs-mount`. If a process
crashes, use `fusermount3 -u /tmp/lmdb-fs-mount`; `-uz` is the deliberate
lazy-unmount recovery option when no process remains responsive.

The full real-mount test is intentionally opt-in:

```bash
LMDB_FS_RUN_FUSE_TESTS=1 uv run pytest -m integration
```

`--cache-size 0` or `--no-cache` disables caching. A cached result is also
bounded by `--cache-max-nodes` (10,000 by default), so a root or broad query
cannot consume the cache with a million virtual file entries.
