from __future__ import annotations

from semanticfs.backends.lmdb_backend import LMDBBackend
from semanticfs.paths import parse_path
from semanticfs.query import SemanticQuery


def test_lmdb_matches_memory_backend(tmp_path, backend, nodes) -> None:  # type: ignore[no-untyped-def]
    index = tmp_path / "index.lmdb"
    LMDBBackend.build(index, nodes)
    lmdb_backend = LMDBBackend(index)
    try:
        lmdb_query = SemanticQuery(lmdb_backend)
        memory_query = SemanticQuery(backend)
        for path in ("", "year=2026", "year=2026/disease=COVID", "lab=missing"):
            predicates = parse_path(path)
            assert lmdb_backend.match(predicates) == backend.match(predicates)
            assert lmdb_query.listing(predicates) == memory_query.listing(predicates)
        assert lmdb_backend.facets == backend.facets
    finally:
        lmdb_backend.close()


def test_lmdb_refuses_accidental_replacement(tmp_path, nodes) -> None:  # type: ignore[no-untyped-def]
    index = tmp_path / "index.lmdb"
    LMDBBackend.build(index, nodes)
    try:
        LMDBBackend.build(index, nodes)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected FileExistsError")
