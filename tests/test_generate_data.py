from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from semanticfs.config import read_nodes_jsonl


def test_generator_is_deterministic_and_correlated(tmp_path) -> None:  # type: ignore[no-untyped-def]
    script = Path(__file__).parents[1] / "tools" / "generate_data.py"
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    for output in (first_dir, second_dir):
        subprocess.run(
            [sys.executable, script, "--nodes", "25", "--seed", "42", "--output", output],
            check=True,
        )
    nodes = list(read_nodes_jsonl(first_dir / "metadata.jsonl"))
    second_nodes = list(read_nodes_jsonl(second_dir / "metadata.jsonl"))
    assert [(node.node_id, node.display_name, node.metadata) for node in nodes] == [
        (node.node_id, node.display_name, node.metadata) for node in second_nodes
    ]
    assert len(nodes) == 25
    assert len(nodes[0].metadata) == 15
    assert nodes[0].metadata["species"] in {"human", "mouse", "hamster"}
    assert json.loads((first_dir / "manifest.json").read_text())["payload_count"] == 100
