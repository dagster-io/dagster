# ruff: noqa: T201
import cProfile
import subprocess
import timeit
from tempfile import TemporaryDirectory

# This script provides a way to measure the performance of instantiating an object.
#
# An example of when this is useful is measuring the impact of changing the backing class
# for a model object from a NamedTuple to a dataclass or pydantic model (DagsterModel).
import memray  # type: ignore
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset

fixed_key = AssetKey("asset_key")


def make_one(i: int = 0):
    """Create an instance of the object you want to profile."""
    return AssetSubset(key=fixed_key, value=False)


def make_n(n: int):
    things = []
    for i in range(n):
        things.append(make_one(i))
    return things


def cpu_profile(n: int):
    print(f"cProfile results for creating {n} objects:\n")
    with cProfile.Profile() as pr:
        make_n(n)
    pr.print_stats(sort="cumtime")


def mem_profile(n: int):
    print(f"memray results for creating {n} objects:\n")
    with TemporaryDirectory() as d:
        f_name = d + "/memray.log"
        with memray.Tracker(f_name):
            _ = make_n(n)

        subprocess.run(["memray", "summary", f_name], check=False)
    print("\n")


def timing() -> int:
    repeat = 5

    print("timeit results:\n")
    t = timeit.Timer(globals=globals(), stmt="make_one()")
    number, _ = t.autorange()
    raw_timings = t.repeat(repeat=repeat, number=number)

    print(
        f"best of {repeat} trials of {number} calls of make_one(): {fmt_time(min(raw_timings) / number)} per call\n"
    )
    return number


def fmt_time(seconds):
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f} ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    else:
        return f"{seconds:.2f} s"


if __name__ == "__main__":
    n = 50_000
    print(f"\nObject profiling for target {make_one()=}\n")
    cpu_profile(n)
    mem_profile(n)
    timing()
