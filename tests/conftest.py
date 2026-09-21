from __future__ import annotations

from pathlib import Path

import pytest

from lmdb_fs.backends.memory import InMemoryBackend
from lmdb_fs.model import Node
from lmdb_fs.query import LMDBFSQuery


@pytest.fixture
def nodes() -> list[Node]:
    rows = [
        (1, "experiment.csv", {"year": "2026", "disease": "COVID", "lab": "LANL", "species": "mouse", "assay": "PCR"}),
        (2, "experiment.csv", {"year": "2026", "disease": "COVID", "lab": "LANL", "species": "human", "assay": "ELISA"}),
        (3, "control.json", {"year": "2026", "disease": "flu", "lab": "Sandia", "species": "mouse", "assay": "PCR"}),
        (4, "pilot report.txt", {"year": "2025", "disease": "COVID", "lab": "Sandia", "species": "mouse", "assay": "ELISA"}),
        (5, "odd/name=%.txt", {"year": "2026", "disease": "COVID", "lab": "LANL", "species": "mouse", "assay": "PCR"}),
    ]
    return [Node(node_id, name, Path(f"/payloads/{node_id}"), metadata) for node_id, name, metadata in rows]


@pytest.fixture
def backend(nodes: list[Node]) -> InMemoryBackend:
    return InMemoryBackend(nodes)


@pytest.fixture
def query(backend: InMemoryBackend) -> LMDBFSQuery:
    return LMDBFSQuery(backend)
