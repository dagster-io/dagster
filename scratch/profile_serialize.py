#!/usr/bin/env python3
"""Profile serialization to find hotspots."""

import cProfile
import pstats
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "dagster"))
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "libraries" / "dagster-shared"))

from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.serdes_fast import serialize_value_fast


def load_small_cursor():
    """Load the small cursor."""
    path = REPO_ROOT / "scratch" / "small_cursor.txt"
    with open(path) as f:
        return deserialize_value(f.read(), AssetDaemonCursor)


def load_full_cursor():
    """Load the full cursor."""
    path = Path("/Users/owen/Downloads/giant_cursor.txt")
    with open(path) as f:
        return deserialize_value(f.read(), AssetDaemonCursor)


def main():
    import sys

    use_full = "--full" in sys.argv

    if use_full:
        cursor = load_full_cursor()
    else:
        cursor = load_small_cursor()
    print(f"Loaded cursor with {len(cursor.previous_condition_cursors)} condition cursors")

    # Profile serialization
    profiler = cProfile.Profile()
    profiler.enable()
    data = serialize_value_fast(cursor)
    profiler.disable()

    print(f"\nSerialized to {len(data):,} bytes")
    print("\nTop 30 functions by cumulative time:")
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(30)


if __name__ == "__main__":
    main()
