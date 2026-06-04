"""Measure the *runtime import closure* of the lite engine.

A tree-shaking packager (PyInstaller/Nuitka) bundles only the modules actually
imported at runtime — not the whole source tree or every installed dependency.
This script runs the real in-process execution path, then sums the on-disk size
of every module left in ``sys.modules``, split into:

  - dagster engine source (the kept core)
  - third-party dependencies actually used
  - stdlib (shipped with the Python runtime, not counted against the engine)

This is the faithful "what the app needs" number — the realistic basis for the
packaged-bundle size.
"""

import os
import sys

# Run the real execution path first so every runtime-reachable module loads.
from dagster import DagsterInstance, asset, job, materialize, op  # noqa: E402


@asset
def upstream() -> int:
    return 21


@asset
def downstream(upstream: int) -> int:
    return upstream * 2


@op
def make_value() -> int:
    return 7


@job
def the_job():
    make_value()


materialize([upstream, downstream], instance=DagsterInstance.ephemeral())
the_job.execute_in_process()

stdlib_dir = os.path.dirname(os.__file__)
site_pkgs = next(p for p in sys.path if p.endswith("site-packages"))
repo_dagster = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "python_modules")
)

buckets: dict[str, int] = {"dagster_engine": 0, "third_party": 0, "stdlib": 0}
counted: set[str] = set()


def add(path: str, bucket: str) -> None:
    if path in counted or not os.path.isfile(path):
        return
    counted.add(path)
    buckets[bucket] += os.path.getsize(path)


for mod in list(sys.modules.values()):
    f = getattr(mod, "__file__", None)
    if not f or not os.path.isfile(f):
        continue
    f = os.path.abspath(f)
    if f.startswith(repo_dagster):
        add(f, "dagster_engine")
    elif f.startswith(site_pkgs):
        add(f, "third_party")
    elif f.startswith(stdlib_dir):
        add(f, "stdlib")
    else:
        add(f, "third_party")

mb = lambda b: f"{b / 1024 / 1024:.2f} MB"  # noqa: E731
shippable = buckets["dagster_engine"] + buckets["third_party"]
print(f"modules loaded         : {len(counted)} files")
print(f"dagster engine source  : {mb(buckets['dagster_engine'])}")
print(f"third-party deps used   : {mb(buckets['third_party'])}")
print(f"stdlib (in runtime)     : {mb(buckets['stdlib'])}")
print(f"--> SHIPPABLE (engine+deps): {mb(shippable)}")
