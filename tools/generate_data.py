#!/usr/bin/env python3
"""Generate a deterministic, correlated lmdb-fs JSONL corpus."""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Iterator
from pathlib import Path

from lmdb_fs.config import write_nodes_jsonl
from lmdb_fs.model import Node

DISEASES = ("COVID", "influenza", "cancer", "diabetes", "malaria", "control")
DISEASE_WEIGHTS = (36, 20, 15, 12, 8, 9)
SPECIES_BY_DISEASE = {
    "COVID": ("human", "mouse", "hamster"),
    "influenza": ("human", "mouse", "ferret"),
    "cancer": ("human", "mouse"),
    "diabetes": ("human", "mouse", "rat"),
    "malaria": ("human", "mouse"),
    "control": ("human", "mouse"),
}
TISSUES = ("blood", "lung", "liver", "brain", "kidney", "tumor", "serum")
GEOGRAPHIES = ("US-CO", "US-NM", "US-CA", "DE-BE", "GB-CAM", "JP-13", "KE-30")
SAMPLE_TYPES = ("biopsy", "swab", "cell-line", "serum", "tissue")
FUNDERS = ("NIH", "DOE", "NSF", "Wellcome", "internal")
PHASES = ("pilot", "discovery", "validation", "longitudinal")


def make_nodes(count: int, seed: int, payloads: tuple[Path, ...]) -> Iterator[Node]:
    rng = random.Random(seed)
    for node_id in range(1, count + 1):
        institution_id = rng.randrange(250)
        institution = f"institution-{institution_id:03d}"
        lab = f"lab-{institution_id:03d}-{rng.randrange(3):02d}"
        disease = rng.choices(DISEASES, weights=DISEASE_WEIGHTS, k=1)[0]
        species = rng.choice(SPECIES_BY_DISEASE[disease])
        assay = rng.choice(("PCR", "sequencing", "ELISA") if lab.endswith(("-00", "-01")) else ("mass-spec", "microscopy", "ELISA"))
        instrument = {
            "PCR": rng.choice(("qPCR-96", "qPCR-384")),
            "sequencing": rng.choice(("NovaSeq", "NextSeq")),
            "ELISA": rng.choice(("SpectraMax", "BioTek")),
            "mass-spec": rng.choice(("Orbitrap", "TripleQuad")),
            "microscopy": rng.choice(("Confocal", "CryoEM")),
        }[assay]
        metadata = {
            "year": str(2007 + rng.randrange(20)),
            "institution": institution,
            "lab": lab,
            "project": f"project-{institution_id:03d}-{rng.randrange(500):04d}",
            "investigator": f"investigator-{institution_id:03d}-{rng.randrange(400):04d}",
            "disease": disease,
            "species": species,
            "tissue": rng.choice(TISSUES),
            "assay": assay,
            "instrument": instrument,
            "protocol": f"{assay.lower()}-v{1 + rng.randrange(8)}",
            "funding_source": rng.choice(FUNDERS),
            "geography": rng.choice(GEOGRAPHIES),
            "sample_type": rng.choice(SAMPLE_TYPES),
            "study_phase": rng.choice(PHASES),
        }
        suffix = ("csv", "json", "txt")[node_id % 3]
        yield Node(
            node_id=node_id,
            display_name=f"experiment-{node_id:08d}.{suffix}",
            payload_path=payloads[(node_id - 1) % len(payloads)],
            metadata=metadata,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True, help="directory for metadata.jsonl and manifest.json")
    parser.add_argument("--seed", type=int, default=20260920)
    parser.add_argument("--payload-count", type=int, default=100)
    args = parser.parse_args()
    if args.nodes <= 0 or args.payload_count <= 0:
        parser.error("--nodes and --payload-count must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    payload_dir = args.output / "payloads"
    payload_dir.mkdir(exist_ok=True)
    payloads = tuple(payload_dir / f"payload-{number:04d}.txt" for number in range(args.payload_count))
    for number, payload in enumerate(payloads):
        payload.write_text(f"lmdb-fs reusable synthetic payload {number}\n", encoding="utf-8")
    write_nodes_jsonl(args.output / "metadata.jsonl", make_nodes(args.nodes, args.seed, payloads))
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "nodes": args.nodes,
                "seed": args.seed,
                "payload_count": args.payload_count,
                "facet_count": 15,
                "metadata": "metadata.jsonl",
                "payload_note": "Payload files are reused; metadata nodes are logical files.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
