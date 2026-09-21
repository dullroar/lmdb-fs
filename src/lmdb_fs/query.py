"""Build virtual directory contents from a backend and predicate key."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from .backends.base import MetadataBackend
from .cache import BoundedLRU, CacheStats
from .model import DirectoryListing, FacetEntry, FileEntry, NodeSet, PredicateKey
from .paths import canonicalize, encode_component


def virtual_filename(node_id: int, display_name: str) -> str:
    """Guarantee a unique, portable virtual filename without losing the name."""

    return f"{node_id}--{encode_component('name', display_name).split('=', 1)[1]}"


class LMDBFSQuery:
    """Pure faceted directory construction; no knowledge of LMDB or FUSE."""

    def __init__(
        self, backend: MetadataBackend, *, cache_size: int = 1_024, cache_max_nodes: int = 10_000
    ) -> None:
        if cache_max_nodes < 0:
            raise ValueError("cache_max_nodes cannot be negative")
        self.backend = backend
        self.cache_max_nodes = cache_max_nodes
        self._match_cache: BoundedLRU[PredicateKey, NodeSet] = BoundedLRU(cache_size)
        self._listing_cache: BoundedLRU[PredicateKey, DirectoryListing] = BoundedLRU(cache_size)
        self._backend_match_ns = 0
        self._remaining_facets_ns = 0
        self._listing_build_ns = 0

    def match(self, predicates: PredicateKey = ()) -> NodeSet:
        """Return a cached canonical match set, timing backend work only."""

        predicates = canonicalize(predicates)
        cached = self._match_cache.get(predicates)
        if cached is not None:
            return cached
        started = perf_counter_ns()
        result = self.backend.match(predicates)
        self._backend_match_ns += perf_counter_ns() - started
        if len(result) <= self.cache_max_nodes:
            self._match_cache.put(predicates, result)
        return result

    def listing(self, predicates: PredicateKey = ()) -> DirectoryListing:
        predicates = canonicalize(predicates)
        cached = self._listing_cache.get(predicates)
        if cached is not None:
            return cached
        started = perf_counter_ns()
        matched = self.match(predicates)
        remaining_started = perf_counter_ns()
        remaining = self.backend.remaining_facets(predicates, matched)
        self._remaining_facets_ns += perf_counter_ns() - remaining_started
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
        result = DirectoryListing(predicates, matched, facets, files)
        self._listing_build_ns += perf_counter_ns() - started
        if len(result.matched_nodes) <= self.cache_max_nodes:
            self._listing_cache.put(predicates, result)
        return result

    def child_predicates(self, predicates: PredicateKey, facet: str, value: str) -> PredicateKey:
        return canonicalize((*predicates, (facet, value)))

    def facet_component(self, entry: FacetEntry) -> str:
        return encode_component(entry.facet, entry.value)

    def metrics(self) -> "QueryMetrics":
        return QueryMetrics(
            backend_match_ns=self._backend_match_ns,
            remaining_facets_ns=self._remaining_facets_ns,
            listing_build_ns=self._listing_build_ns,
            match_cache=self._match_cache.stats(),
            listing_cache=self._listing_cache.stats(),
        )


@dataclass(frozen=True, slots=True)
class QueryMetrics:
    backend_match_ns: int
    remaining_facets_ns: int
    listing_build_ns: int
    match_cache: CacheStats
    listing_cache: CacheStats
