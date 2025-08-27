import os
import time
import warnings
from dataclasses import dataclass
from functools import lru_cache

import pytest

try:
    from dagster import BetaWarning, PreviewWarning, SupersessionWarning

    warnings.filterwarnings("ignore", category=BetaWarning)
    warnings.filterwarnings("ignore", category=PreviewWarning)
    warnings.filterwarnings("ignore", category=SupersessionWarning)
except ImportError:
    pass  # Not all test suites have dagster installed


@dataclass(frozen=True)
class TestId:
    scope: str
    name: str


@lru_cache
def buildkite_quarantined_tests(annotation) -> set[TestId]:
    quarantined_tests = set()

    if os.getenv("BUILDKITE") or os.getenv("LOCAL_BUILDKITE_QUARANTINE"):
        # Run our full test suite - warts and all - on the release branch
        if os.getenv("BUILDKITE_BRANCH", "").startswith("release-"):
            return quarantined_tests

        try:
            import requests

            token = os.getenv("BUILDKITE_TEST_QUARANTINE_TOKEN")
            org_slug = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
            suite_slug = os.getenv("BUILDKITE_TEST_SUITE_SLUG")

            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://api.buildkite.com/v2/analytics/organizations/{org_slug}/suites/{suite_slug}/tests/{annotation}"

            start_time = time.time()
            timeout = 10

            while url and time.time() - start_time < timeout:
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                for test in response.json():
                    scope = test.get("scope", "")
                    name = test.get("name", "")
                    quarantined_test = TestId(scope, name)

                    quarantined_tests.add(quarantined_test)

                link_header = response.headers.get("Link", "")
                next_url = None
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        next_url = part[part.find("<") + 1 : part.find(">")]
                        break

                url = next_url

        except Exception as e:
            print(e)  # noqa

    return quarantined_tests


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
    # https://buildkite.com/docs/apis/rest-api/test-engine/quarantine#list-quarantined-tests
    # Buildkite Test Engine marks unreliable tests as muted and triages them out to owning teams to improve.
    # We pull this list of tests at the beginning of each pytest session and add soft xfail markers to each
    # quarantined test.
    try:
        muted = buildkite_quarantined_tests("muted")
        skipped = buildkite_quarantined_tests("skipped")
        if muted or skipped:
            # https://github.com/buildkite/test-collector-python/blob/6fba081a2844d6bdec8607942eee48a03d60cd40/src/buildkite_test_collector/pytest_plugin/buildkite_plugin.py#L22-L27
            chunks = item.nodeid.split("::")
            scope = "::".join(chunks[:-1])
            name = chunks[-1]

            test = TestId(scope, name)

            if test in muted:
                item.add_marker(pytest.mark.xfail(reason="Test muted in Buildkite.", strict=False))
            if test in skipped:
                item.add_marker(pytest.skip(reason="Test skipped in Buildkite."))
    except Exception as e:
        print(e)  # noqa

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
