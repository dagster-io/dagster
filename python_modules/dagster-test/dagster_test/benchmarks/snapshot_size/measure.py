# ruff: noqa: T201
"""Measure the serialized repository snapshot of the posttrain-like mock definitions.

Usage: python -m dagster_test.benchmarks.snapshot_size.measure [--out snapshot.json]
"""

import argparse
import gzip
import json
import time
from collections import Counter

from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._serdes import deserialize_value, serialize_value

from dagster_test.benchmarks.snapshot_size.posttrain_like_defs import build_definitions


def _size(value) -> int:
    return len(json.dumps(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    parser.add_argument("--breakdown", action="store_true")
    args = parser.parse_args()

    start = time.perf_counter()
    repo = build_definitions().get_repository_def()
    repo.load_all_definitions()
    built = time.perf_counter()
    snap = RepositorySnap.from_def(repo, defer_snapshots=True)
    snapped = time.perf_counter()
    serialized = serialize_value(snap)
    serialized_at = time.perf_counter()
    roundtrip = deserialize_value(serialized, RepositorySnap)
    deserialized_at = time.perf_counter()
    raw = serialized.encode()
    print(
        f"assets={len(snap.asset_nodes)} checks={len(snap.asset_check_nodes or [])}"
        f" bytes={len(raw)} gzip={len(gzip.compress(raw, 6))}"
    )
    print(
        f"build={built - start:.1f}s snap={snapped - built:.1f}s"
        f" serialize={serialized_at - snapped:.1f}s deserialize={deserialized_at - serialized_at:.1f}s"
    )
    assert len(roundtrip.asset_nodes) == len(snap.asset_nodes)
    if args.out:
        with open(args.out, "wb") as f:
            f.write(raw)
    if args.breakdown:
        top = json.loads(serialized)
        for key, value in sorted(top.items(), key=lambda kv: -_size(kv[1])):
            fields: Counter = Counter()
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            fields[k] += _size(v)
            print(f"  {key}: {_size(value)} {fields.most_common(8)}")


if __name__ == "__main__":
    main()
