#!/usr/bin/env python3
"""Debug roundtrip issues."""

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "dagster"))
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "libraries" / "dagster-shared"))

import msgpack
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.serdes_fast import deserialize_value_fast, serialize_value_fast


def compute_expected_hash(ts, tz):
    """Compute what the hash should be for a TimestampWithTimezone."""
    # This mirrors the hashing logic in serdes_fast.py
    from dagster._core.definitions.timestamp import TimestampWithTimezone

    obj = TimestampWithTimezone(ts, tz)
    full_repr = f"TimestampWithTimezone:{obj!r}"
    return hashlib.md5(full_repr.encode()).hexdigest()[:16]


def main():
    # Load cursor
    path = REPO_ROOT / "scratch" / "small_cursor.txt"
    with open(path) as f:
        cursor = deserialize_value(f.read(), AssetDaemonCursor)

    print(f"Loaded cursor with {len(cursor.previous_condition_cursors)} condition cursors")

    # Collect all unique timestamps from original cursor
    original_timestamps = set()
    from dataclasses import (
        fields as dataclass_fields,
        is_dataclass,
    )

    from dagster_shared.record import (
        as_dict as record_as_dict,
        is_record,
    )

    def collect_timestamps(obj):
        if obj is None:
            return
        class_name = type(obj).__name__
        if class_name == "TimestampWithTimezone":
            original_timestamps.add((obj.timestamp, obj.timezone))
            return

        if is_record(obj):
            for k, v in record_as_dict(obj).items():
                collect_timestamps(v)
        elif is_dataclass(obj) and not isinstance(obj, type):
            for f in dataclass_fields(obj):
                v = getattr(obj, f.name)
                collect_timestamps(v)
        elif hasattr(obj, "_asdict"):
            for k, v in obj._asdict().items():
                collect_timestamps(v)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                collect_timestamps(v)
        elif isinstance(obj, (list, tuple)) and not hasattr(obj, "_fields"):
            for v in obj:
                collect_timestamps(v)

    collect_timestamps(cursor)
    print(f"Original unique timestamps: {len(original_timestamps)}")

    # Serialize with fast
    data = serialize_value_fast(cursor)
    print(f"\nSerialized to {len(data)} bytes")

    # Unpack msgpack to see structure
    envelope = msgpack.unpackb(data, raw=False, strict_map_key=False)

    # Get TimestampWithTimezone class index
    ts_class_idx = envelope["s"]["c"].index("TimestampWithTimezone")
    ts_field_idx = envelope["s"]["f"].index("timestamp")
    tz_field_idx = envelope["s"]["f"].index("timezone")

    print(
        f"TimestampWithTimezone class idx: {ts_class_idx}, field idxs: timestamp={ts_field_idx}, timezone={tz_field_idx}"
    )

    # Extract timestamps from objects table
    packed_timestamps = {}
    for h, obj in envelope["o"].items():
        if obj.get("@") == ts_class_idx:
            ts = obj.get(ts_field_idx)
            tz_val = obj.get(tz_field_idx)
            # Resolve interned string
            if isinstance(tz_val, dict) and "~" in tz_val:
                tz_val = envelope["t"][tz_val["~"]]
            packed_timestamps[h] = (ts, tz_val)

    print(f"Objects table unique timestamps: {len(packed_timestamps)}")

    # Check if all original timestamps are in the objects table
    missing = []
    for ts, tz in original_timestamps:
        expected_hash = compute_expected_hash(ts, tz)
        if expected_hash not in packed_timestamps:
            missing.append((ts, tz, expected_hash))

    if missing:
        print(f"\n!!! MISSING {len(missing)} timestamps from objects table !!!")
        for ts, tz, h in missing[:10]:
            print(f"  {ts} ({tz}) -> hash {h}")
    else:
        print("\nAll original timestamps found in objects table.")

    # Look for the specific failing timestamp
    target_ts = 1722236400.0
    found = [(h, ts, tz) for h, (ts, tz) in packed_timestamps.items() if ts == target_ts]
    print(f"\nObjects with timestamp {target_ts}: {found}")

    wrong_ts = 1425369600.0
    found2 = [(h, ts, tz) for h, (ts, tz) in packed_timestamps.items() if ts == wrong_ts]
    print(f"Objects with timestamp {wrong_ts}: {found2}")

    # Count references in packed data
    def count_refs(val, ref_counts):
        if isinstance(val, dict):
            if "#" in val and len(val) == 1:
                ref_counts[val["#"]] = ref_counts.get(val["#"], 0) + 1
            else:
                for v in val.values():
                    count_refs(v, ref_counts)
        elif isinstance(val, list):
            for v in val:
                count_refs(v, ref_counts)

    ref_counts = {}
    count_refs(envelope["d"], ref_counts)
    print(f"\nTotal object references in data: {sum(ref_counts.values())}")

    # Find embedded TimestampWithTimezone objects (not in objects table)
    def find_embedded_ts(val, path="root"):
        results = []
        if isinstance(val, dict):
            if "@" in val and val.get("@") == ts_class_idx:
                ts = val.get(ts_field_idx)
                tz = val.get(tz_field_idx)
                if isinstance(tz, dict) and "~" in tz:
                    tz = envelope["t"][tz["~"]]
                results.append((path, ts, tz))
            elif "#" not in val:  # Not a reference
                for k, v in val.items():
                    results.extend(find_embedded_ts(v, f"{path}.{k}"))
        elif isinstance(val, list):
            for i, v in enumerate(val):
                results.extend(find_embedded_ts(v, f"{path}[{i}]"))
        return results

    embedded = find_embedded_ts(envelope["d"])
    print(f"\nEmbedded TimestampWithTimezone in data (not refs): {len(embedded)}")
    for path, ts, tz in embedded[:10]:
        expected_hash = compute_expected_hash(ts, tz)
        in_table = "YES" if expected_hash in packed_timestamps else "NO"
        print(f"  {ts} ({tz}) at {path[:80]}... -> in table: {in_table}")

    # Deserialize and compare
    cursor2 = deserialize_value_fast(data, AssetDaemonCursor)

    # Collect timestamps from roundtripped cursor
    roundtrip_timestamps = set()

    def collect_rt_timestamps(obj):
        if obj is None:
            return
        class_name = type(obj).__name__
        if class_name == "TimestampWithTimezone":
            roundtrip_timestamps.add((obj.timestamp, obj.timezone))
            return

        if is_record(obj):
            for k, v in record_as_dict(obj).items():
                collect_rt_timestamps(v)
        elif is_dataclass(obj) and not isinstance(obj, type):
            for f in dataclass_fields(obj):
                v = getattr(obj, f.name)
                collect_rt_timestamps(v)
        elif hasattr(obj, "_asdict"):
            for k, v in obj._asdict().items():
                collect_rt_timestamps(v)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                collect_rt_timestamps(v)
        elif isinstance(obj, (list, tuple)) and not hasattr(obj, "_fields"):
            for v in obj:
                collect_rt_timestamps(v)

    collect_rt_timestamps(cursor2)

    # Check what's different
    in_orig_not_roundtrip = original_timestamps - roundtrip_timestamps
    in_roundtrip_not_orig = roundtrip_timestamps - original_timestamps

    if in_orig_not_roundtrip:
        print(f"\nTimestamps in original but NOT in roundtrip: {len(in_orig_not_roundtrip)}")
        for ts, tz in list(in_orig_not_roundtrip)[:5]:
            print(f"  {ts} ({tz})")

    if in_roundtrip_not_orig:
        print(f"\nTimestamps in roundtrip but NOT in original: {len(in_roundtrip_not_orig)}")
        for ts, tz in list(in_roundtrip_not_orig)[:5]:
            print(f"  {ts} ({tz})")

    # Check for dangling references (references to hashes not in objects table)
    def find_dangling_refs(val, path="root"):
        results = []
        if isinstance(val, dict):
            if "#" in val and len(val) == 1:
                obj_hash = val["#"]
                if obj_hash not in envelope["o"]:
                    results.append((path, obj_hash))
            else:
                for k, v in val.items():
                    results.extend(find_dangling_refs(v, f"{path}.{k}"))
        elif isinstance(val, list):
            for i, v in enumerate(val):
                results.extend(find_dangling_refs(v, f"{path}[{i}]"))
        return results

    dangling = find_dangling_refs(envelope["d"])
    print(f"\nDangling references (hash not in objects table): {len(dangling)}")
    for path, h in dangling[:10]:
        print(f"  {h} at {path[:80]}")

    # Count all TS references
    def count_ts_refs(val):
        count = 0
        if isinstance(val, dict):
            if "#" in val and len(val) == 1:
                obj_hash = val["#"]
                if obj_hash in envelope["o"] and envelope["o"][obj_hash].get("@") == ts_class_idx:
                    count += 1
            else:
                for v in val.values():
                    count += count_ts_refs(v)
        elif isinstance(val, list):
            for v in val:
                count += count_ts_refs(v)
        return count

    ts_ref_count = count_ts_refs(envelope["d"])
    print(f"\nTimestampWithTimezone references in data: {ts_ref_count}")
    print(f"Total TS in data (embedded + refs): {len(embedded) + ts_ref_count}")

    # Find WHERE the missing timestamps appear in the original cursor
    missing_ts_set = set(in_orig_not_roundtrip)
    print(f"\n=== Tracing {len(missing_ts_set)} missing timestamps in original ===")

    def find_ts_locations(obj, path="cursor"):
        results = []
        if obj is None:
            return results
        class_name = type(obj).__name__
        if class_name == "TimestampWithTimezone":
            if (obj.timestamp, obj.timezone) in missing_ts_set:
                results.append((path, obj.timestamp, obj.timezone))
            return results

        if is_record(obj):
            for k, v in record_as_dict(obj).items():
                results.extend(find_ts_locations(v, f"{path}.{k}"))
        elif is_dataclass(obj) and not isinstance(obj, type):
            for f in dataclass_fields(obj):
                v = getattr(obj, f.name)
                results.extend(find_ts_locations(v, f"{path}.{f.name}"))
        elif hasattr(obj, "_asdict"):
            for k, v in obj._asdict().items():
                results.extend(find_ts_locations(v, f"{path}.{k}"))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                results.extend(find_ts_locations(v, f"{path}[{repr(k)[:30]}]"))
        elif isinstance(obj, (list, tuple)) and not hasattr(obj, "_fields"):
            for i, v in enumerate(obj):
                results.extend(find_ts_locations(v, f"{path}[{i}]"))
        return results

    locations = find_ts_locations(cursor)
    print(f"Found {len(locations)} missing timestamp locations:")
    for path, ts, tz in locations[:20]:
        print(f"  {ts} at {path}")


if __name__ == "__main__":
    main()
