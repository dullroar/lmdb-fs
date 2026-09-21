"""Per-mount inode identities for virtual paths and file appearances."""

from __future__ import annotations

from dataclasses import dataclass

import pyfuse3

from ..model import PredicateKey


@dataclass(frozen=True, slots=True)
class DirectoryRef:
    predicates: PredicateKey
    parent_inode: int | None


@dataclass(frozen=True, slots=True)
class FileRef:
    node_id: int
    parent_inode: int


InodeRef = DirectoryRef | FileRef


class InodeTable:
    """Stable mounted-session inode allocation.

    A query directory is keyed by both canonical predicates and its visible
    parent. This preserves POSIX ``..`` behavior for alternate facet orders
    while the query result itself remains order-independent.
    """

    def __init__(self) -> None:
        self._next_inode = int(pyfuse3.ROOT_INODE) + 1
        self._by_inode: dict[int, InodeRef] = {int(pyfuse3.ROOT_INODE): DirectoryRef((), None)}
        self._directory_keys: dict[tuple[PredicateKey, int | None], int] = {((), None): int(pyfuse3.ROOT_INODE)}
        self._file_keys: dict[tuple[int, int], int] = {}

    def get(self, inode: int) -> InodeRef:
        try:
            return self._by_inode[int(inode)]
        except KeyError as exc:
            raise KeyError(f"unknown inode {inode}") from exc

    def directory(self, predicates: PredicateKey, parent_inode: int) -> int:
        key = (predicates, parent_inode)
        existing = self._directory_keys.get(key)
        if existing is not None:
            return existing
        inode = self._allocate(DirectoryRef(predicates, parent_inode))
        self._directory_keys[key] = inode
        return inode

    def file(self, node_id: int, parent_inode: int) -> int:
        key = (node_id, parent_inode)
        existing = self._file_keys.get(key)
        if existing is not None:
            return existing
        inode = self._allocate(FileRef(node_id, parent_inode))
        self._file_keys[key] = inode
        return inode

    def _allocate(self, ref: InodeRef) -> int:
        inode = self._next_inode
        self._next_inode += 1
        self._by_inode[inode] = ref
        return inode
