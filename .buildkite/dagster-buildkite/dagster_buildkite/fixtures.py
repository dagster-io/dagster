import os
from dataclasses import dataclass
from functools import lru_cache

import pytest


@dataclass(frozen=True)
class TestId:
    scope: str
    name: str


@lru_cache
def buildkite_quarantined_tests() -> set[TestId]:
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
            url = f"https://api.buildkite.com/v2/analytics/organizations/{org_slug}/suites/{suite_slug}/tests/muted"

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            for test in response.json():
                scope = test.get("scope", "")
                name = test.get("name", "")
                quarantined_test = TestId(scope, name)

                quarantined_tests.add(quarantined_test)

        except Exception as e:
            print(e)  # noqa

    return quarantined_tests


def pytest_runtest_setup(item):
    # https://buildkite.com/docs/apis/rest-api/test-engine/quarantine#list-quarantined-tests
    # Buildkite Test Engine marks unreliable tests as muted and triages them out to owning teams to improve.
    # We pull this list of tests at the beginning of each pytest session and add soft xfail markers to each
    # quarantined test.
    try:
        if buildkite_quarantined_tests():
            # https://github.com/buildkite/test-collector-python/blob/6fba081a2844d6bdec8607942eee48a03d60cd40/src/buildkite_test_collector/pytest_plugin/buildkite_plugin.py#L22-L27
            chunks = item.nodeid.split("::")
            scope = "::".join(chunks[:-1])
            name = chunks[-1]

            test = TestId(scope, name)

            if test in buildkite_quarantined_tests():
                item.add_marker(
                    pytest.mark.xfail(reason="Test muted in Buildkite.", strict=False)
                )
    except Exception as e:
        print(e)  # noqa
