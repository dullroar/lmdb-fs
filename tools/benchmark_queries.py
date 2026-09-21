#!/usr/bin/env python3
"""Benchmark lmdb-fs query and directory construction without FUSE."""

from __future__ import annotations

import argparse
import json
import math
import resource
import statistics
import time
from dataclasses import asdict
from pathlib import Path

from lmdb_fs.backends.lmdb_backend import LMDBBackend
from lmdb_fs.query import LMDBFSQuery


def percentile(values: list[int], point: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(point * len(ordered)) - 1)]


def index_size(path: Path) -> int:
    return sum(entry.stat().st_size for entry in path.rglob("*") if entry.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--cache-size", type=int, default=1024)
    parser.add_argument("--cache-max-nodes", type=int, default=10_000)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--baseline-scan", action="store_true", help="also scan all records for each probe")
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("--iterations must be positive")
    backend = LMDBBackend(args.db)
    try:
        sample = backend.get_node(1)
        ordered_facets = ("year", "disease", "lab", "species", "assay")
        cases = {
            "one": tuple((facet, sample.metadata[facet]) for facet in ordered_facets[:1]),
            "two": tuple((facet, sample.metadata[facet]) for facet in ordered_facets[:2]),
            "three": tuple((facet, sample.metadata[facet]) for facet in ordered_facets[:3]),
            "five": tuple((facet, sample.metadata[facet]) for facet in ordered_facets),
            "high_cardinality": (("investigator", sample.metadata["investigator"]),),
            "zero_result": (("year", "0000"),),
        }
        cache_size = 0 if args.no_cache else args.cache_size
        query = LMDBFSQuery(backend, cache_size=cache_size, cache_max_nodes=args.cache_max_nodes)
        report: dict[str, object] = {
            "db": str(args.db),
            "index_bytes": index_size(args.db),
            "iterations": args.iterations,
            "cache_size": cache_size,
            "cache_max_nodes": args.cache_max_nodes,
            "cases": {},
        }
        for label, predicates in cases.items():
            latencies: list[int] = []
            result_size = 0
            for iteration in range(args.iterations):
                rotated = predicates[iteration % len(predicates) :] + predicates[: iteration % len(predicates)]
                started = time.perf_counter_ns()
                listing = query.listing(rotated)
                latencies.append(time.perf_counter_ns() - started)
                result_size = len(listing.matched_nodes)
            report["cases"][label] = {
                "predicates": predicates,
                "result_size": result_size,
                "median_ns": int(statistics.median(latencies)),
                "p95_ns": percentile(latencies, 0.95),
                "p99_ns": percentile(latencies, 0.99),
                "queries_per_second": round(1_000_000_000 / statistics.mean(latencies), 2),
            }
        if args.baseline_scan:
            probe = cases["three"]
            started = time.perf_counter_ns()
            matching = [
                node.node_id
                for node in backend.get_nodes(backend.all_node_ids())
                if all(node.metadata.get(facet) == value for facet, value in probe)
            ]
            report["baseline_scan"] = {
                "predicates": probe,
                "result_size": len(matching),
                "elapsed_ns": time.perf_counter_ns() - started,
            }
        report["metrics"] = asdict(query.metrics())
        report["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print(json.dumps(report, indent=2, sort_keys=True))
    finally:
        backend.close()


if __name__ == "__main__":
    main()
