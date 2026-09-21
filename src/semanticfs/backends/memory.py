"""Simple indexed backend used for semantics tests and as an oracle for LMDB."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from ..model import Node, NodeSet, PredicateKey
from .base import MetadataBackend


class InMemoryBackend(MetadataBackend):
    """Immutable inverted index with smallest-posting-list intersection."""

    def __init__(self, nodes: Iterable[Node]) -> None:
        self._nodes = {node.node_id: node for node in nodes}
        if not self._nodes:
            raise ValueError("backend needs at least one node")
        self._postings: dict[tuple[str, str], NodeSet] = {}
        mutable: dict[tuple[str, str], set[int]] = defaultdict(set)
        facets: set[str] = set()
        for node in self._nodes.values():
            facets.update(node.metadata)
            for item in node.metadata.items():
                mutable[item].add(node.node_id)
        self._postings = {key: frozenset(ids) for key, ids in mutable.items()}
        self._facets = frozenset(facets)
        self._all = frozenset(self._nodes)

    @property
    def facets(self) -> frozenset[str]:
        return self._facets

    def all_node_ids(self) -> NodeSet:
        return self._all

    def match(self, predicates: PredicateKey) -> NodeSet:
        postings = [self._postings.get(predicate, frozenset()) for predicate in predicates]
        if not postings:
            return self._all
        postings.sort(key=len)
        result = postings[0]
        for posting in postings[1:]:
            result = result.intersection(posting)
            if not result:
                break
        return frozenset(result)

    def remaining_facets(
        self, predicates: PredicateKey, matched_nodes: NodeSet
    ) -> Mapping[str, Mapping[str, int]]:
        used = {facet for facet, _ in predicates}
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for node_id in matched_nodes:
            for facet, value in self._nodes[node_id].metadata.items():
                if facet not in used:
                    counts[facet][value] += 1
        return {facet: dict(values) for facet, values in counts.items()}

    def get_node(self, node_id: int) -> Node:
        return self._nodes[node_id]

    def get_nodes(self, node_ids: Iterable[int]) -> Iterable[Node]:
        return (self._nodes[node_id] for node_id in node_ids)
