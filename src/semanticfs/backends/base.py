"""Backend boundary deliberately independent of FUSE."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Protocol

from ..model import Node, NodeSet, PredicateKey


class MetadataBackend(Protocol):
    """Read-only interface required by the semantic query layer."""

    @property
    def facets(self) -> frozenset[str]: ...

    def all_node_ids(self) -> NodeSet: ...

    def match(self, predicates: PredicateKey) -> NodeSet: ...

    def remaining_facets(
        self, predicates: PredicateKey, matched_nodes: NodeSet
    ) -> Mapping[str, Mapping[str, int]]: ...

    def get_node(self, node_id: int) -> Node: ...

    def get_nodes(self, node_ids: Iterable[int]) -> Iterable[Node]: ...
