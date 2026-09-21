from __future__ import annotations

import asyncio
import errno
from pathlib import Path

import pyfuse3
import pytest

from lmdb_fs.backends.memory import InMemoryBackend
from lmdb_fs.fuse.operations import LMDBFSOperations
from lmdb_fs.model import Node
from lmdb_fs.query import LMDBFSQuery


def _operations(tmp_path: Path) -> LMDBFSOperations:
    payload = tmp_path / "payload.txt"
    payload.write_text("payload through fuse\n")
    node = Node(
        7,
        "payload.txt",
        payload,
        {"year": "2026", "disease": "COVID", "lab": "LANL"},
    )
    return LMDBFSOperations(LMDBFSQuery(InMemoryBackend([node])), stat_path=tmp_path)


def test_operations_expose_directory_and_payload(tmp_path: Path) -> None:
    ops = _operations(tmp_path)
    root_entries = ops._children(pyfuse3.ROOT_INODE)
    year_name, year_inode = next(entry for entry in root_entries if entry[0] == b"year=2026")
    assert year_name == b"year=2026"
    assert asyncio.run(ops.lookup(pyfuse3.ROOT_INODE, year_name, None)).st_ino == year_inode

    files = ops._children(year_inode)
    _, file_inode = next(entry for entry in files if entry[0].startswith(b"7--"))
    attrs = asyncio.run(ops.getattr(file_inode))
    assert attrs.st_size == len(b"payload through fuse\n")
    info = asyncio.run(ops.open(file_inode, 0, None))
    try:
        assert asyncio.run(ops.read(info.fh, 0, 7)) == b"payload"
    finally:
        asyncio.run(ops.release(info.fh))


def test_direct_facet_lookup_does_not_enumerate_parent(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    ops = _operations(tmp_path)

    def fail_listing(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("lookup must not enumerate a broad parent")

    monkeypatch.setattr(ops.query, "listing", fail_listing)
    attrs = asyncio.run(ops.lookup(pyfuse3.ROOT_INODE, b"year=2026", None))
    assert attrs.st_mode & 0o170000 == 0o040000


def test_opendir_keeps_and_releases_a_snapshot(tmp_path: Path) -> None:
    ops = _operations(tmp_path)
    handle = asyncio.run(ops.opendir(pyfuse3.ROOT_INODE, None))
    assert int(handle) in ops._open_dirs
    asyncio.run(ops.releasedir(handle))
    assert int(handle) not in ops._open_dirs


@pytest.mark.parametrize("operation", ["mkdir", "unlink", "rmdir"])
def test_mutations_report_erofs(tmp_path: Path, operation: str) -> None:
    ops = _operations(tmp_path)
    method = getattr(ops, operation)
    args = {
        "mkdir": (pyfuse3.ROOT_INODE, b"new", 0o755, None),
        "unlink": (pyfuse3.ROOT_INODE, b"new", None),
        "rmdir": (pyfuse3.ROOT_INODE, b"new", None),
    }[operation]
    with pytest.raises(pyfuse3.FUSEError) as exc:
        asyncio.run(method(*args))
    assert exc.value.errno == errno.EROFS
