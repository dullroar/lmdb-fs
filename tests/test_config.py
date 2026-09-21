from __future__ import annotations

from semanticfs.config import read_nodes_jsonl, write_nodes_jsonl


def test_jsonl_round_trip(tmp_path, nodes) -> None:  # type: ignore[no-untyped-def]
    metadata = tmp_path / "nodes.jsonl"
    write_nodes_jsonl(metadata, nodes)
    assert list(read_nodes_jsonl(metadata)) == nodes
