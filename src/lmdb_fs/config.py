"""Boring file-format and mount configuration helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from .model import Node


def read_nodes_jsonl(path: Path | str) -> Iterator[Node]:
    """Read the documented JSONL exchange format with useful line errors."""

    source = Path(path)
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                metadata = row["metadata"]
                if not isinstance(metadata, dict):
                    raise TypeError("metadata must be an object")
                yield Node(
                    node_id=int(row["node_id"]),
                    display_name=str(row["display_name"]),
                    payload_path=Path(row["payload_path"]),
                    metadata={str(key): str(value) for key, value in metadata.items()},
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid metadata at {source}:{line_number}: {exc}") from exc


def write_nodes_jsonl(path: Path | str, nodes: Iterable[Node]) -> None:
    """Write a deterministic JSONL corpus manifest input."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as stream:
        for node in nodes:
            row = {
                "node_id": node.node_id,
                "display_name": node.display_name,
                "payload_path": str(node.payload_path),
                "metadata": dict(sorted(node.metadata.items())),
            }
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
