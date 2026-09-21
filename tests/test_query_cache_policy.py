from __future__ import annotations

from lmdb_fs.query import LMDBFSQuery


def test_large_results_are_not_cached(backend) -> None:  # type: ignore[no-untyped-def]
    query = LMDBFSQuery(backend, cache_size=10, cache_max_nodes=1)
    query.listing()
    query.listing()
    assert query.metrics().listing_cache.hits == 0
