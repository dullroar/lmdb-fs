from __future__ import annotations

from semanticfs.cache import BoundedLRU
from semanticfs.paths import parse_path


def test_bounded_lru_evicts_least_recent_and_counts() -> None:
    cache: BoundedLRU[str, int] = BoundedLRU(1)
    assert cache.get("missing") is None
    cache.put("one", 1)
    assert cache.get("one") == 1
    cache.put("two", 2)
    assert cache.get("one") is None
    assert cache.stats().evictions == 1


def test_query_cache_is_shared_by_path_order(query) -> None:  # type: ignore[no-untyped-def]
    query.listing(parse_path("year=2026/disease=COVID"))
    query.listing(parse_path("disease=COVID/year=2026"))
    metrics = query.metrics()
    assert metrics.listing_cache.hits == 1
    assert metrics.listing_cache.misses == 1
