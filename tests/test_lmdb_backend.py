from __future__ import annotations

from lmdb_fs.backends.lmdb_backend import LMDBBackend
from lmdb_fs.paths import parse_path
from lmdb_fs.query import LMDBFSQuery


def test_lmdb_matches_memory_backend(tmp_path, backend, nodes) -> None:  # type: ignore[no-untyped-def]
    index = tmp_path / "index.lmdb"
    LMDBBackend.build(index, nodes)
    lmdb_backend = LMDBBackend(index)
    try:
        lmdb_query = LMDBFSQuery(lmdb_backend)
        memory_query = LMDBFSQuery(backend)
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
