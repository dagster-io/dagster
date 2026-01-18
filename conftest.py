import os
import warnings

import pytest

try:
    from dagster import BetaWarning, PreviewWarning, SupersessionWarning

    warnings.filterwarnings("ignore", category=BetaWarning)
    warnings.filterwarnings("ignore", category=PreviewWarning)
    warnings.filterwarnings("ignore", category=SupersessionWarning)
except ImportError:
    pass  # Not all test suites have dagster installed


def pytest_addoption(parser):
    parser.addoption(
        "--split", action="store", default=None, help="Split test selection (e.g., 0/3)"
    )


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


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """Split pytest collection.

    Example usage:

    pytest --split 1/2 # run half the tests
    pytest --split 2/2 # run the other half the tests
    """
    split_option = config.getoption("--split")
    if not split_option:
        return

    try:
        k, n = map(int, split_option.split("/"))
    except ValueError:
        raise pytest.UsageError(
            "--split must be in the form numerator/denominator (e.g. --split=1/3)"
        )

    if k <= 0:
        raise pytest.UsageError("--split numerator must be > 0")

    if k > n:
        raise pytest.UsageError("--split numerator must be smaller than denominator")

    total = len(items)
    start = total * (k - 1) // n
    end = total * k // n

    selected = items[start:end]
    deselected = items[:start] + items[end:]

    if deselected:
        config.hook.pytest_deselected(items=deselected)

    items[:] = selected
