from __future__ import annotations

import asyncio
import errno
from pathlib import Path

import pyfuse3
import pytest

from semanticfs.backends.memory import InMemoryBackend
from semanticfs.fuse.operations import SemanticFSOperations
from semanticfs.model import Node
from semanticfs.query import SemanticQuery


def _operations(tmp_path: Path) -> SemanticFSOperations:
    payload = tmp_path / "payload.txt"
    payload.write_text("payload through fuse\n")
    node = Node(
        7,
        "payload.txt",
        payload,
        {"year": "2026", "disease": "COVID", "lab": "LANL"},
    )
    return SemanticFSOperations(SemanticQuery(InMemoryBackend([node])), stat_path=tmp_path)


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
