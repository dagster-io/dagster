import importlib.util
import os
import warnings

import pytest


# Register pytest plugins shipped inside dagster. Scoping registration here
# (rather than via a pytest11 entry point on the dagster distribution) keeps
# these plugins from auto-loading for downstream users who `pip install
# dagster` and run their own pytest suite. Guarded on the plugin module itself
# being importable, not just on `dagster`: test envs under this rootdir that
# don't install dagster (e.g. the .buildkite/ tox envs) and those that install
# a released dagster predating this module (e.g. the *-pypi example suites)
# both lack it, and must not fail at conftest load time.
def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ImportError:
        # A parent package (e.g. `dagster`) isn't importable in this env.
        return False


pytest_plugins = (
    ["dagster._utils.test.quarantine"]
    if _module_available("dagster._utils.test.quarantine")
    else []
)

# We have to define these warnings filters here instead of in
# static config because the dagster package is not guaranteed to be installed
# in all test suites that use this conftest.py.
try:
    from dagster import BetaWarning, PreviewWarning, SupersessionWarning

    warnings.filterwarnings("ignore", category=BetaWarning)
    warnings.filterwarnings("ignore", category=PreviewWarning)
    warnings.filterwarnings("ignore", category=SupersessionWarning)
except ImportError:
    pass  # Not all test suites have dagster installed


def pytest_configure(config):
    # Create a section break in the logs any time Buildkite invokes pytest
    # https://buildkite.com/docs/pipelines/managing-log-output
    # https://docs.pytest.org/en/7.1.x/reference/reference.html?highlight=pytest_configure#pytest.hookspec.pytest_configure
    if os.getenv("BUILDKITE"):
        print("+++ Running :pytest: PyTest")  # noqa


def pytest_runtest_setup(item):
    try:
        next(item.iter_markers("integration"))
        if os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
            pytest.skip("Integration tests are disabled")

    except StopIteration:
        pass
