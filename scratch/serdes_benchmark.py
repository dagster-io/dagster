#!/usr/bin/env python3
"""Benchmark script for serdes optimizations.

Usage:
    python scratch/serdes_benchmark.py

This script loads the giant cursor, creates a smaller version for fast iteration,
and provides benchmarking/profiling utilities.
"""

import cProfile
import dataclasses
import io
import os
import pstats
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Add dagster to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "dagster"))
sys.path.insert(0, str(REPO_ROOT / "python_modules" / "libraries" / "dagster-shared"))

# Import dagster serdes
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster_shared.serdes import deserialize_value, serialize_value
from dagster_shared.serdes.serdes_fast import deserialize_value_fast, serialize_value_fast

# Configuration
GIANT_CURSOR_PATH = Path(
    os.environ.get("GIANT_CURSOR_PATH", "/Users/owen/Downloads/giant_cursor.txt")
)
SMALL_CURSOR_PATH = REPO_ROOT / "scratch" / "small_cursor.txt"


def load_giant_cursor_json() -> str:
    """Load the raw JSON string from the giant cursor file."""
    print(f"Loading giant cursor from {GIANT_CURSOR_PATH}...")
    start = time.time()
    with open(GIANT_CURSOR_PATH) as f:
        data = f.read()
    elapsed = time.time() - start
    print(f"  Loaded {len(data):,} bytes in {elapsed:.2f}s")
    return data


def load_giant_cursor() -> AssetDaemonCursor:
    """Load and deserialize the giant cursor."""
    json_str = load_giant_cursor_json()
    print("Deserializing cursor...")
    start = time.time()
    cursor = deserialize_value(json_str, AssetDaemonCursor)
    elapsed = time.time() - start
    print(f"  Deserialized in {elapsed:.2f}s")
    return cursor


def create_small_cursor(cursor: AssetDaemonCursor, fraction: int = 20) -> AssetDaemonCursor:
    """Create a smaller cursor by taking 1/fraction of the previous_condition_cursors."""
    if cursor.previous_condition_cursors is None:
        return cursor

    n_original = len(cursor.previous_condition_cursors)
    n_small = max(1, n_original // fraction)

    # Take evenly spaced samples
    step = n_original / n_small
    indices = [int(i * step) for i in range(n_small)]
    small_cursors = [cursor.previous_condition_cursors[i] for i in indices]

    small_cursor = dataclasses.replace(cursor, previous_condition_cursors=small_cursors)
    print(f"Created small cursor: {n_original} -> {n_small} condition cursors")
    return small_cursor


def save_cursor(cursor: AssetDaemonCursor, path: Path) -> None:
    """Serialize and save a cursor to a file."""
    print(f"Saving cursor to {path}...")
    start = time.time()
    json_str = serialize_value(cursor)
    elapsed = time.time() - start
    print(f"  Serialized in {elapsed:.2f}s ({len(json_str):,} bytes)")
    with open(path, "w") as f:
        f.write(json_str)


def load_cursor(path: Path) -> AssetDaemonCursor:
    """Load a cursor from a file."""
    with open(path) as f:
        json_str = f.read()
    return deserialize_value(json_str, AssetDaemonCursor)


def benchmark(name: str, fn: Callable[[], Any], iterations: int = 5, warmup: int = 1) -> dict:
    """Benchmark a function with multiple iterations."""
    results = {"name": name, "iterations": iterations, "times": []}

    # Warmup
    for _ in range(warmup):
        fn()

    # Timed runs
    for i in range(iterations):
        start = time.time()
        result = fn()
        elapsed = time.time() - start
        results["times"].append(elapsed)

    results["min"] = min(results["times"])
    results["max"] = max(results["times"])
    results["avg"] = sum(results["times"]) / len(results["times"])

    print(
        f"{name}: avg={results['avg']:.3f}s, min={results['min']:.3f}s, max={results['max']:.3f}s"
    )
    return results


def profile_function(fn: Callable[[], Any], name: str = "profile") -> pstats.Stats:
    """Profile a function and return stats."""
    profiler = cProfile.Profile()
    profiler.enable()
    fn()
    profiler.disable()

    # Get stats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")

    print(f"\n=== Profile: {name} ===")
    stats.print_stats(30)
    print(stream.getvalue())

    return stats


def verify_equality(original: AssetDaemonCursor, roundtripped: AssetDaemonCursor) -> bool:
    """Verify that roundtripped cursor equals the original."""
    # Serialize both and compare
    orig_json = serialize_value(original)
    rt_json = serialize_value(roundtripped)

    if orig_json == rt_json:
        print("  Equality check: PASSED")
        return True
    else:
        print("  Equality check: FAILED")
        # Find where they differ
        for i, (a, b) in enumerate(zip(orig_json, rt_json)):
            if a != b:
                print(f"  First difference at position {i}")
                print(f"    Original: {orig_json[max(0, i - 50) : i + 50]!r}")
                print(f"    Roundtripped: {rt_json[max(0, i - 50) : i + 50]!r}")
                break
        return False


def cursor_stats(cursor: AssetDaemonCursor) -> dict:
    """Get statistics about a cursor."""
    stats = {
        "evaluation_id": cursor.evaluation_id,
        "n_observe_timestamps": len(cursor.last_observe_request_timestamp_by_asset_key),
        "n_condition_cursors": len(cursor.previous_condition_cursors)
        if cursor.previous_condition_cursors
        else 0,
    }

    # Count node cursors
    if cursor.previous_condition_cursors:
        total_node_cursors = sum(
            len(cc.node_cursors_by_unique_id) for cc in cursor.previous_condition_cursors
        )
        stats["total_node_cursors"] = total_node_cursors

    return stats


def benchmark_serialize(cursor: AssetDaemonCursor, iterations: int = 3) -> dict:
    """Benchmark serialization."""
    result = {}

    def serialize():
        return serialize_value(cursor)

    # First run to get output size
    json_str = serialize()
    result["output_size_bytes"] = len(json_str)
    result["output_size_mb"] = len(json_str) / (1024 * 1024)

    # Benchmark
    bench = benchmark("serialize", serialize, iterations=iterations)
    result.update(bench)

    return result


def benchmark_deserialize(json_str: str, iterations: int = 3) -> dict:
    """Benchmark deserialization."""

    def deserialize():
        return deserialize_value(json_str, AssetDaemonCursor)

    return benchmark("deserialize", deserialize, iterations=iterations)


def run_full_benchmark(cursor: AssetDaemonCursor, name: str = "cursor") -> dict:
    """Run full benchmark suite on a cursor."""
    print(f"\n{'=' * 60}")
    print(f"Benchmarking: {name}")
    print(f"{'=' * 60}")

    stats = cursor_stats(cursor)
    print(f"Cursor stats: {stats}")

    results = {"name": name, "stats": stats}

    # Serialize benchmark
    print("\n--- Serialization ---")
    results["serialize"] = benchmark_serialize(cursor)

    # Get serialized form for deserialize benchmark
    json_str = serialize_value(cursor)

    # Deserialize benchmark
    print("\n--- Deserialization ---")
    results["deserialize"] = benchmark_deserialize(json_str)

    # Roundtrip verification
    print("\n--- Roundtrip Verification ---")
    roundtripped = deserialize_value(json_str, AssetDaemonCursor)
    results["roundtrip_equal"] = verify_equality(cursor, roundtripped)

    return results


def benchmark_fast_serialize(cursor: AssetDaemonCursor, iterations: int = 3) -> dict:
    """Benchmark fast serialization."""
    result = {}

    def serialize():
        return serialize_value_fast(cursor)

    # First run to get output size
    data = serialize()
    result["output_size_bytes"] = len(data)
    result["output_size_mb"] = len(data) / (1024 * 1024)

    # Benchmark
    bench = benchmark("serialize_fast", serialize, iterations=iterations)
    result.update(bench)

    return result


def benchmark_fast_deserialize(data: bytes, iterations: int = 3) -> dict:
    """Benchmark fast deserialization."""

    def deserialize():
        return deserialize_value_fast(data, AssetDaemonCursor)

    return benchmark("deserialize_fast", deserialize, iterations=iterations)


def verify_fast_equality(original: AssetDaemonCursor, roundtripped: AssetDaemonCursor) -> bool:
    """Verify that fast roundtripped cursor equals the original."""
    # Serialize both with standard serdes and compare
    orig_json = serialize_value(original)
    rt_json = serialize_value(roundtripped)

    if orig_json == rt_json:
        print("  Fast equality check: PASSED")
        return True
    else:
        print("  Fast equality check: FAILED")
        # Find where they differ
        for i, (a, b) in enumerate(zip(orig_json, rt_json)):
            if a != b:
                print(f"  First difference at position {i}")
                print(f"    Original: {orig_json[max(0, i - 50) : i + 50]!r}")
                print(f"    Roundtripped: {rt_json[max(0, i - 50) : i + 50]!r}")
                break
        if len(orig_json) != len(rt_json):
            print(f"  Length difference: {len(orig_json)} vs {len(rt_json)}")
        return False


def run_fast_benchmark(cursor: AssetDaemonCursor, name: str = "cursor") -> dict:
    """Run benchmark suite for fast serializer."""
    print(f"\n{'=' * 60}")
    print(f"Fast Benchmark: {name}")
    print(f"{'=' * 60}")

    stats = cursor_stats(cursor)
    print(f"Cursor stats: {stats}")

    results = {"name": name, "stats": stats}

    # Serialize benchmark
    print("\n--- Fast Serialization ---")
    results["serialize"] = benchmark_fast_serialize(cursor)

    # Get serialized form for deserialize benchmark
    data = serialize_value_fast(cursor)

    # Deserialize benchmark
    print("\n--- Fast Deserialization ---")
    results["deserialize"] = benchmark_fast_deserialize(data)

    # Roundtrip verification
    print("\n--- Fast Roundtrip Verification ---")
    try:
        roundtripped = deserialize_value_fast(data, AssetDaemonCursor)
        results["roundtrip_equal"] = verify_fast_equality(cursor, roundtripped)
    except Exception as e:
        print(f"  Fast roundtrip FAILED with error: {e}")
        results["roundtrip_equal"] = False
        results["error"] = str(e)

    return results


def compare_results(original: dict, fast: dict) -> None:
    """Compare benchmark results and print summary."""
    print(f"\n{'=' * 60}")
    print("Comparison")
    print(f"{'=' * 60}")

    # Size comparison
    orig_size = original["serialize"]["output_size_mb"]
    fast_size = fast["serialize"]["output_size_mb"]
    size_reduction = (1 - fast_size / orig_size) * 100

    print("\nSize:")
    print(f"  Original: {orig_size:.2f} MB")
    print(f"  Fast:     {fast_size:.2f} MB")
    print(f"  Reduction: {size_reduction:.1f}%")

    # Speed comparison
    orig_ser = original["serialize"]["avg"]
    fast_ser = fast["serialize"]["avg"]
    ser_speedup = orig_ser / fast_ser

    print("\nSerialize time:")
    print(f"  Original: {orig_ser:.3f}s")
    print(f"  Fast:     {fast_ser:.3f}s")
    print(f"  Speedup:  {ser_speedup:.2f}x")

    orig_des = original["deserialize"]["avg"]
    fast_des = fast["deserialize"]["avg"]
    des_speedup = orig_des / fast_des

    print("\nDeserialize time:")
    print(f"  Original: {orig_des:.3f}s")
    print(f"  Fast:     {fast_des:.3f}s")
    print(f"  Speedup:  {des_speedup:.2f}x")

    # Correctness
    print("\nCorrectness:")
    print(f"  Original roundtrip: {'PASS' if original['roundtrip_equal'] else 'FAIL'}")
    print(f"  Fast roundtrip:     {'PASS' if fast['roundtrip_equal'] else 'FAIL'}")


def main():
    """Main benchmark runner."""
    print("=" * 60)
    print("Serdes Benchmark Suite")
    print("=" * 60)

    # Load the giant cursor
    giant_cursor = load_giant_cursor()

    # Create small cursor for fast iteration
    small_cursor = create_small_cursor(giant_cursor, fraction=20)

    # Save small cursor for future runs
    if not SMALL_CURSOR_PATH.exists():
        save_cursor(small_cursor, SMALL_CURSOR_PATH)

    # Run standard benchmarks
    print("\n" + "=" * 60)
    print("Running STANDARD benchmarks on SMALL cursor")
    print("=" * 60)
    small_results = run_full_benchmark(small_cursor, "small_cursor")

    # Run fast benchmarks
    print("\n" + "=" * 60)
    print("Running FAST benchmarks on SMALL cursor")
    print("=" * 60)
    small_fast_results = run_fast_benchmark(small_cursor, "small_cursor_fast")

    # Compare
    compare_results(small_results, small_fast_results)

    # Optionally run on full cursor
    run_full = os.environ.get("BENCHMARK_FULL", "").lower() in ("1", "true", "yes")
    if run_full:
        print("\n" + "=" * 60)
        print("Running STANDARD benchmarks on FULL cursor")
        print("=" * 60)
        full_results = run_full_benchmark(giant_cursor, "giant_cursor")

        print("\n" + "=" * 60)
        print("Running FAST benchmarks on FULL cursor")
        print("=" * 60)
        full_fast_results = run_fast_benchmark(giant_cursor, "giant_cursor_fast")

        # Compare full
        compare_results(full_results, full_fast_results)

    print("\n" + "=" * 60)
    print("Final Summary")
    print("=" * 60)
    print(f"\nSmall cursor ({small_results['stats']['n_condition_cursors']} cursors):")
    print(
        f"  Standard: serialize={small_results['serialize']['avg']:.3f}s, deserialize={small_results['deserialize']['avg']:.3f}s, size={small_results['serialize']['output_size_mb']:.2f}MB"
    )
    print(
        f"  Fast:     serialize={small_fast_results['serialize']['avg']:.3f}s, deserialize={small_fast_results['deserialize']['avg']:.3f}s, size={small_fast_results['serialize']['output_size_mb']:.2f}MB"
    )

    if run_full:
        print(f"\nFull cursor ({full_results['stats']['n_condition_cursors']} cursors):")
        print(
            f"  Standard: serialize={full_results['serialize']['avg']:.3f}s, deserialize={full_results['deserialize']['avg']:.3f}s, size={full_results['serialize']['output_size_mb']:.2f}MB"
        )
        print(
            f"  Fast:     serialize={full_fast_results['serialize']['avg']:.3f}s, deserialize={full_fast_results['deserialize']['avg']:.3f}s, size={full_fast_results['serialize']['output_size_mb']:.2f}MB"
        )


if __name__ == "__main__":
    main()
