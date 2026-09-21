"""LMDB-backed inverted metadata index.

Posting lists use LMDB duplicate values instead of one giant serialized blob:
each ``(facet, value)`` key maps to sorted, fixed-width node-ID duplicates.
That keeps an individual LMDB value small even for common facet values.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

import lmdb

from ..model import Node, NodeSet, PredicateKey
from .base import MetadataBackend

_NODE_ID = struct.Struct(">Q")
_META_FACETS = b"facets"


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _posting_key(facet: str, value: str) -> bytes:
    return _json([facet, value])


def _facet_key(facet: str) -> bytes:
    return _json(facet)


def _node_key(node_id: int) -> bytes:
    return _NODE_ID.pack(node_id)


def _decode_node(raw: bytes) -> Node:
    data = json.loads(raw)
    return Node(
        node_id=data["node_id"],
        display_name=data["display_name"],
        payload_path=Path(data["payload_path"]),
        metadata=data["metadata"],
    )


class LMDBBackend(MetadataBackend):
    """Read-only metadata backend over a prebuilt LMDB environment."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._env = lmdb.open(
            os.fspath(self.path),
            readonly=True,
            lock=False,
            max_dbs=4,
            subdir=True,
            readahead=True,
        )
        self._nodes_db = self._env.open_db(b"nodes")
        self._postings_db = self._env.open_db(b"facet_postings", dupsort=True)
        self._facet_values_db = self._env.open_db(b"facet_values", dupsort=True)
        self._metadata_db = self._env.open_db(b"metadata")
        with self._env.begin(db=self._metadata_db) as txn:
            raw_facets = txn.get(_META_FACETS)
        if raw_facets is None:
            self.close()
            raise ValueError(f"{self.path} is not a SemanticFS index")
        self._facets = frozenset(json.loads(raw_facets))

    @classmethod
    def build(
        cls,
        path: Path | str,
        nodes: Iterable[Node],
        *,
        map_size: int = 1 << 30,
        replace: bool = False,
    ) -> None:
        """Build a new index; refuse replacement unless explicitly requested."""

        target = Path(path)
        node_list = list(nodes)
        if not node_list:
            raise ValueError("cannot build an index without nodes")
        ids = [node.node_id for node in node_list]
        if len(ids) != len(set(ids)):
            raise ValueError("node IDs must be unique")
        if target.exists():
            if not replace:
                raise FileExistsError(f"index already exists: {target}")
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        env = lmdb.open(os.fspath(target), map_size=map_size, max_dbs=4, subdir=True)
        try:
            nodes_db = env.open_db(b"nodes")
            postings_db = env.open_db(b"facet_postings", dupsort=True)
            facet_values_db = env.open_db(b"facet_values", dupsort=True)
            metadata_db = env.open_db(b"metadata")
            facets: set[str] = set()
            with env.begin(write=True) as txn:
                for node in node_list:
                    node_data = {
                        "node_id": node.node_id,
                        "display_name": node.display_name,
                        "payload_path": os.fspath(node.payload_path),
                        "metadata": dict(sorted(node.metadata.items())),
                    }
                    if not txn.put(_node_key(node.node_id), _json(node_data), db=nodes_db, overwrite=False):
                        raise ValueError(f"duplicate node ID {node.node_id}")
                    for facet, value in node.metadata.items():
                        facets.add(facet)
                        txn.put(
                            _posting_key(facet, value),
                            _node_key(node.node_id),
                            db=postings_db,
                            dupdata=True,
                        )
                        txn.put(_facet_key(facet), value.encode("utf-8"), db=facet_values_db, dupdata=True)
                txn.put(_META_FACETS, _json(sorted(facets)), db=metadata_db)
                txn.put(b"node_count", str(len(node_list)).encode("ascii"), db=metadata_db)
        finally:
            env.close()

    @property
    def facets(self) -> frozenset[str]:
        return self._facets

    def close(self) -> None:
        self._env.close()

    def all_node_ids(self) -> NodeSet:
        with self._env.begin(db=self._nodes_db) as txn:
            with txn.cursor() as cursor:
                return frozenset(_NODE_ID.unpack(key)[0] for key, _ in cursor)

    def _posting(self, txn: lmdb.Transaction, predicate: tuple[str, str]) -> NodeSet:
        with txn.cursor(db=self._postings_db) as cursor:
            if not cursor.set_key(_posting_key(*predicate)):
                return frozenset()
            return frozenset(_NODE_ID.unpack(value)[0] for value in cursor.iternext_dup(keys=False))

    def match(self, predicates: PredicateKey) -> NodeSet:
        if not predicates:
            return self.all_node_ids()
        with self._env.begin() as txn:
            postings = [self._posting(txn, predicate) for predicate in predicates]
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
        with self._env.begin(db=self._nodes_db) as txn:
            for node_id in matched_nodes:
                raw = txn.get(_node_key(node_id))
                if raw is None:
                    raise KeyError(node_id)
                for facet, value in json.loads(raw)["metadata"].items():
                    if facet not in used:
                        counts[facet][value] += 1
        return {facet: dict(values) for facet, values in counts.items()}

    def get_node(self, node_id: int) -> Node:
        with self._env.begin(db=self._nodes_db) as txn:
            raw = txn.get(_node_key(node_id))
        if raw is None:
            raise KeyError(node_id)
        return _decode_node(raw)

    def get_nodes(self, node_ids: Iterable[int]) -> Iterable[Node]:
        requested = tuple(node_ids)
        with self._env.begin(db=self._nodes_db) as txn:
            nodes = []
            for node_id in requested:
                raw = txn.get(_node_key(node_id))
                if raw is None:
                    raise KeyError(node_id)
                nodes.append(_decode_node(raw))
        return tuple(nodes)
