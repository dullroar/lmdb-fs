#!/usr/bin/env python3
"""Measure ordinary directory enumeration against a mounted SemanticFS path."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path


def percentile(values: list[int], point: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(point * len(ordered)) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+", help="mounted directories to enumerate")
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("--iterations must be positive")
    report: dict[str, object] = {"iterations": args.iterations, "paths": {}}
    for path in args.paths:
        latencies: list[int] = []
        entry_count = 0
        for _ in range(args.iterations):
            started = time.perf_counter_ns()
            entries = list(path.iterdir())
            latencies.append(time.perf_counter_ns() - started)
            entry_count = len(entries)
        report["paths"][str(path)] = {
            "entries": entry_count,
            "median_ns": int(statistics.median(latencies)),
            "p95_ns": percentile(latencies, 0.95),
            "p99_ns": percentile(latencies, 0.99),
        }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
