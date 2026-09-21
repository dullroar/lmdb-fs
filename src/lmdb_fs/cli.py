"""Command-line entry point for building, mounting, and unmounting lmdb-fs."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import pyfuse3
import trio

from .backends.lmdb_backend import LMDBBackend
from .config import read_nodes_jsonl
from .fuse.operations import LMDBFSOperations
from .query import LMDBFSQuery


def _map_size_gib(value: str) -> int:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return int(number * 1024**3)


def _build_index(args: argparse.Namespace) -> int:
    LMDBBackend.build(args.db, read_nodes_jsonl(args.metadata), map_size=args.map_size, replace=args.replace)
    return 0


def _mount(args: argparse.Namespace) -> int:
    backend = LMDBBackend(args.db)
    cache_size = 0 if args.no_cache else args.cache_size
    operations = LMDBFSOperations(
        LMDBFSQuery(backend, cache_size=cache_size, cache_max_nodes=args.cache_max_nodes), stat_path=args.db
    )
    options = set(pyfuse3.default_options)
    options.add("fsname=lmdb-fs")
    if args.debug:
        options.add("debug")
    pyfuse3.init(operations, os.fspath(args.mountpoint), options)
    try:
        trio.run(pyfuse3.main)
    finally:
        pyfuse3.close(unmount=False)
        backend.close()
    return 0


def _unmount(args: argparse.Namespace) -> int:
    subprocess.run(["fusermount3", "-u", os.fspath(args.mountpoint)], check=True)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="lmdb-fs", description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-index", help="build an LMDB index from JSONL metadata")
    build.add_argument("--metadata", type=Path, required=True)
    build.add_argument("--db", type=Path, required=True)
    build.add_argument("--map-size-gib", dest="map_size", type=_map_size_gib, default=4 * 1024**3)
    build.add_argument("--replace", action="store_true", help="replace an existing index")
    build.set_defaults(handler=_build_index)

    mount = commands.add_parser("mount", help="mount a read-only lmdb-fs index")
    mount.add_argument("--db", type=Path, required=True)
    mount.add_argument("--mountpoint", type=Path, required=True)
    mount.add_argument("--debug", action="store_true")
    mount.add_argument("--cache-size", type=int, default=1024)
    mount.add_argument("--cache-max-nodes", type=int, default=10_000)
    mount.add_argument("--no-cache", action="store_true")
    mount.set_defaults(handler=_mount)

    unmount = commands.add_parser("unmount", help="unmount an lmdb-fs mount")
    unmount.add_argument("--mountpoint", type=Path, required=True)
    unmount.set_defaults(handler=_unmount)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
