"""Build virtual directory contents from a backend and predicate key."""

from __future__ import annotations

from .backends.base import MetadataBackend
from .model import DirectoryListing, FacetEntry, FileEntry, PredicateKey
from .paths import canonicalize, encode_component


def virtual_filename(node_id: int, display_name: str) -> str:
    """Guarantee a unique, portable virtual filename without losing the name."""

    return f"{node_id}--{encode_component('name', display_name).split('=', 1)[1]}"


class SemanticQuery:
    """Pure faceted directory construction; no knowledge of LMDB or FUSE."""

    def __init__(self, backend: MetadataBackend) -> None:
        self.backend = backend

    def listing(self, predicates: PredicateKey = ()) -> DirectoryListing:
        predicates = canonicalize(predicates)
        matched = self.backend.match(predicates)
        remaining = self.backend.remaining_facets(predicates, matched)
        facets = tuple(
            FacetEntry(facet, value, count)
            for facet in sorted(remaining)
            for value, count in sorted(remaining[facet].items())
            if count > 0
        )
        files = tuple(
            FileEntry(node.node_id, virtual_filename(node.node_id, node.display_name))
            for node in sorted(self.backend.get_nodes(matched), key=lambda node: node.node_id)
        )
        return DirectoryListing(predicates, matched, facets, files)

    def child_predicates(self, predicates: PredicateKey, facet: str, value: str) -> PredicateKey:
        return canonicalize((*predicates, (facet, value)))

    def facet_component(self, entry: FacetEntry) -> str:
        return encode_component(entry.facet, entry.value)
