#!/usr/bin/env python3
"""Debug hash collisions."""

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "dagster"))
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "libraries" / "dagster-shared"))

from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.serdes import deserialize_value


def main():
    # Load cursor
    path = REPO_ROOT / "scratch" / "small_cursor.txt"
    with open(path) as f:
        cursor = deserialize_value(f.read(), AssetDaemonCursor)

    # Collect all TimestampWithTimezone objects
    from collections import defaultdict

    timestamps = []
    hashes = defaultdict(list)

    from dataclasses import (
        fields as dataclass_fields,
        is_dataclass,
    )

    from dagster_shared.record import (
        as_dict as record_as_dict,
        is_record,
    )

    def collect_timestamps(obj, path=""):
        if obj is None:
            return
        class_name = type(obj).__name__
        if class_name == "TimestampWithTimezone":
            r = repr(obj)
            full_repr = f"{class_name}:{r}"
            h = hashlib.md5(full_repr.encode()).hexdigest()[:16]
            timestamps.append((h, r, path))
            hashes[h].append((r, path))
            return

        if is_record(obj):
            for k, v in record_as_dict(obj).items():
                collect_timestamps(v, f"{path}.{k}")
        elif is_dataclass(obj) and not isinstance(obj, type):
            for f in dataclass_fields(obj):
                v = getattr(obj, f.name)
                collect_timestamps(v, f"{path}.{f.name}")
        elif hasattr(obj, "_asdict"):
            for k, v in obj._asdict().items():
                collect_timestamps(v, f"{path}.{k}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                collect_timestamps(v, f"{path}[{k}]")
        elif isinstance(obj, (list, tuple)) and not hasattr(obj, "_fields"):
            for i, v in enumerate(obj):
                collect_timestamps(v, f"{path}[{i}]")

    collect_timestamps(cursor, "cursor")

    print(f"Found {len(timestamps)} TimestampWithTimezone objects")
    print(f"Unique hashes: {len(hashes)}")

    # Find collisions
    collisions = {h: vs for h, vs in hashes.items() if len(vs) > 1}
    print(f"Hashes with collisions: {len(collisions)}")

    if collisions:
        for h, vs in list(collisions.items())[:5]:
            print(f"\nCollision for hash {h}:")
            unique_reprs = set(r for r, _ in vs)
            if len(unique_reprs) > 1:
                print(f"  REAL COLLISION - {len(unique_reprs)} unique values!")
                for r, p in vs[:5]:
                    print(f"    {r[:100]}")
            else:
                print(f"  Same value appearing {len(vs)} times (not a collision)")


if __name__ == "__main__":
    main()
