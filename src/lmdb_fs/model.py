"""Core immutable types shared by lmdb-fs layers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, TypeAlias

Predicate: TypeAlias = tuple[str, str]
PredicateKey: TypeAlias = tuple[Predicate, ...]
NodeSet: TypeAlias = frozenset[int]


@dataclass(frozen=True, slots=True)
class Node:
    """One immutable payload and the metadata that indexes it."""

    node_id: int
    display_name: str
    payload_path: Path
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.node_id < 0:
            raise ValueError("node_id must be non-negative")
        if not self.display_name:
            raise ValueError("display_name must not be empty")
        if not self.metadata:
            raise ValueError("metadata must not be empty")
        for facet, value in self.metadata.items():
            if not facet or not isinstance(facet, str):
                raise ValueError("metadata facet names must be non-empty strings")
            if not isinstance(value, str) or not value:
                raise ValueError("metadata values must be non-empty strings")


@dataclass(frozen=True, slots=True)
class FacetEntry:
    """A navigable, nonempty facet/value child directory."""

    facet: str
    value: str
    count: int


@dataclass(frozen=True, slots=True)
class FileEntry:
    """A virtual appearance of a node in a query directory."""

    node_id: int
    name: str


@dataclass(frozen=True, slots=True)
class DirectoryListing:
    """The complete contents generated for one canonical predicate set."""

    predicates: PredicateKey
    matched_nodes: NodeSet
    facets: tuple[FacetEntry, ...]
    files: tuple[FileEntry, ...]
