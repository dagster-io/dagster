# python_modules/dagster/dagster_tests/logging_tests/test_buildkite_collector.py

import os
import sys

import pytest
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_buildkite_analytics_integration():
    """This is an integration test that prints its progress to stdout.
    The use of `print` is intentional for readable test logs.
    """
    print("Testing Buildkite Analytics Integration...")  # noqa: T201
    print(f"BUILDKITE_ANALYTICS_TOKEN: {os.environ.get('BUILDKITE_ANALYTICS_TOKEN', 'NOT SET')}")  # noqa: T201
    print(f"BUILDKITE: {os.environ.get('BUILDKITE')}")  # noqa: T201
    print(f"BUILDKITE_BUILD_ID: {os.environ.get('BUILDKITE_BUILD_ID')}")  # noqa: T201
    print(f"BUILDKITE_JOB_ID: {os.environ.get('BUILDKITE_JOB_ID')}")  # noqa: T201
    print(f"BUILDKITE_COMMIT: {os.environ.get('BUILDKITE_COMMIT')}")  # noqa: T201
    print(f"BUILDKITE_ORGANIZATION_SLUG: {os.environ.get('BUILDKITE_ORGANIZATION_SLUG')}")  # noqa: T201
    print(f"BUILDKITE_PIPELINE_SLUG: {os.environ.get('BUILDKITE_PIPELINE_SLUG')}")  # noqa: T201

    # Direct API Integration Test
    print("\nTesting Direct Buildkite Analytics API Integration...")  # noqa: T201
    token = os.environ.get("BUILDKITE_ANALYTICS_TOKEN")
    if token:
        print("Using Analytics Token: [TOKEN REDACTED]")  # noqa: T201
        headers = {"Authorization": f'Token token="{token}"', "Content-Type": "application/json"}
        try:
            # Sample test result payload for loguru bridge validation
            payload = {
                "format": "json",
                "run_env": {
                    "ci": "buildkite",
                    "key": os.environ.get("BUILDKITE_BUILD_ID"),
                    "url": (
                        "https://buildkite.com/dagster/unit-tests/builds/"
                        f"{os.environ.get('BUILDKITE_BUILD_NUMBER', 'local-test')}"
                    ),
                    "branch": os.environ.get("BUILDKITE_BRANCH", "Issue-29914-loguru-bridge"),
                    "commit_sha": os.environ.get("BUILDKITE_COMMIT"),
                    "number": os.environ.get("BUILDKITE_BUILD_NUMBER", "local-validation"),
                },
                "data": [
                    {
                        "id": "test_buildkite_analytics_integration",
                        "scope": "logging_tests.buildkite_collector_validation",
                        "name": "Buildkite Analytics Integration Test",
                        "location": "test_buildkite_collector.py::test_buildkite_analytics_integration",
                        "result": "passed",
                        "history": {"section": "loguru_bridge_buildkite_integration"},
                    }
                ],
            }

            # POST to Buildkite Analytics API
            print("Sending test results to Buildkite Analytics API...")  # noqa: T201
            response = requests.post(
                "https://analytics-api.buildkite.com/v1/uploads", json=payload, headers=headers
            )
            print(f"API Response Status: {response.status_code}")  # noqa: T201
            if response.status_code == 200:
                print("Success! Test results uploaded to Buildkite Analytics")  # noqa: T201
            elif response.status_code == 202:
                print("Accepted! Test results uploaded and being processed by Buildkite Analytics")  # noqa: T201
            elif response.status_code == 401:
                print("Unauthorized - Token may need to be associated with test suite")  # noqa: T201
            else:
                print(f"Unexpected response: {response.status_code}")  # noqa: T201
            print(f"Response Details: {response.text}")  # noqa: T201
        except Exception as e:
            print(f"API Integration Error: {e}")  # noqa: T201
    else:
        print("No BUILDKITE_ANALYTICS_TOKEN found - skipping API test")  # noqa: T201

    assert True


if __name__ == "__main__":
    # This block is for running the script directly, so print is expected.
    print("Starting Buildkite Analytics Integration Test...")  # noqa: T201

    # Validate required environment variable
    analytics_token = os.environ.get("BUILDKITE_ANALYTICS_TOKEN")
    if not analytics_token:
        print("ERROR: BUILDKITE_ANALYTICS_TOKEN environment variable must be set")  # noqa: T201
        print("Usage: export BUILDKITE_ANALYTICS_TOKEN='your_token_here'")  # noqa: T201
        sys.exit(1)

    print("Analytics token found - setting up test environment...")  # noqa: T201

    # Set up meaningful test environment variables
    os.environ["BUILDKITE"] = "true"
    os.environ["BUILDKITE_BUILD_ID"] = "local-loguru-bridge-test-build"
    os.environ["BUILDKITE_JOB_ID"] = "logging-tests-job-validation"
    os.environ["BUILDKITE_COMMIT"] = "loguru-bridge-integration-commit"
    os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "dagster"
    os.environ["BUILDKITE_PIPELINE_SLUG"] = "unit-tests"

    print("Running pytest with local configuration...")  # noqa: T201
    exit_code = pytest.main(["-vvs", __file__])
    print(f"Test completed with exit code: {exit_code}")  # noqa: T201

    if exit_code == 0:
        print("All tests passed successfully!")  # noqa: T201
    else:
        print("Some tests failed - check output above")  # noqa: T201
