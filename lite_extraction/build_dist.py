"""Build a runnable deployable bundle of the lite engine.

Runs the real in-process execution path to discover which top-level packages
are used, then copies each one *in full* (minus __pycache__, *.dist-info, and
test directories) into ``lite_extraction/dist/lite_dagster/``. Copying whole
packages — rather than only the individually-loaded files — keeps
dynamically-imported submodules present, so the bundle actually runs. This is
the tree-shaken engine+deps a packager ships, excluding the Python runtime.
"""

import os
import shutil
import sys

from dagster import DagsterInstance, asset, job, materialize, op


@asset
def upstream() -> int:
    return 21


@asset
def downstream(upstream: int) -> int:
    return upstream * 2


@op
def seven() -> int:
    return 7


@job
def j():
    seven()


materialize([upstream, downstream], instance=DagsterInstance.ephemeral())
j.execute_in_process()

# Discover used top-level packages. For each, resolve its on-disk location
# directly from the top-level module object (robust on Windows, where path
# case can differ from sys.path entries). Skip stdlib (ships with the runtime).
stdlib_dir = os.path.dirname(os.__file__).lower()
top_names: set[str] = set()
for mod in list(sys.modules.values()):
    f = getattr(mod, "__file__", None)
    if not f or not os.path.isfile(f):
        continue
    low = os.path.abspath(f).lower()
    if low.startswith(stdlib_dir) and "site-packages" not in low:
        continue
    top = mod.__name__.split(".")[0]
    if top in ("_virtualenv", "lite_extraction", "__main__", "dagster_pipes_tests"):
        continue
    top_names.add(top)

here = os.path.dirname(os.path.abspath(__file__))
dist = os.path.join(here, "dist", "lite_dagster")
if os.path.isdir(dist):
    shutil.rmtree(dist)
os.makedirs(dist)

_IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*_tests", "*_tests_*", "test", "tests"
)


def copy_top(top: str) -> bool:
    mod = sys.modules.get(top)
    # Package with a directory: copy the whole package dir.
    paths = list(getattr(mod, "__path__", []) or [])
    if paths and os.path.isdir(paths[0]):
        shutil.copytree(paths[0], os.path.join(dist, top), ignore=_IGNORE, dirs_exist_ok=True)
        return True
    # Single-file module.
    f = getattr(mod, "__file__", None)
    if f and f.endswith(".py") and os.path.isfile(f):
        shutil.copy2(f, os.path.join(dist, os.path.basename(f)))
        return True
    return False  # extension module (.pyd) — part of the runtime, skip


for top in sorted(top_names):
    copy_top(top)

total = sum(
    os.path.getsize(os.path.join(dp, fn))
    for dp, _, fns in os.walk(dist)
    for fn in fns
)
copied = sorted(d for d in os.listdir(dist))
print("bundled top-level packages:", ", ".join(copied))
print(f"bundle size (engine + deps, no pyc/tests): {total / 1024 / 1024:.2f} MB")
