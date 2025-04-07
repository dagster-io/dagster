import os

import pytest


def pytest_configure(config):
    # Create a section break in the logs any time Buildkite invokes pytest
    # https://buildkite.com/docs/pipelines/managing-log-output
    # https://docs.pytest.org/en/7.1.x/reference/reference.html?highlight=pytest_configure#pytest.hookspec.pytest_configure
    if os.getenv("BUILDKITE"):
        print("+++ Running :pytest: PyTest")  # noqa

    # https://docs.pytest.org/en/7.1.x/example/markers.html#custom-marker-and-command-line-option-to-control-test-runs
    config.addinivalue_line(
        "markers", "integration: mark test to skip if DISABLE_INTEGRATION_TESTS is set."
    )


def pytest_runtest_setup(item):
    try:
        next(item.iter_markers("integration"))
        if os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
            pytest.skip("Integration tests are disabled")

    except StopIteration:
        pass
