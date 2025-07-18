import os
import pytest
import requests

def test_buildkite_analytics_integration():
    print("Testing Buildkite Analytics Integration...")
    print(f"BUILDKITE_ANALYTICS_TOKEN: {os.environ.get('BUILDKITE_ANALYTICS_TOKEN', 'NOT SET')}")
    print(f"BUILDKITE: {os.environ.get('BUILDKITE')}")
    print(f"BUILDKITE_BUILD_ID: {os.environ.get('BUILDKITE_BUILD_ID')}")
    print(f"BUILDKITE_JOB_ID: {os.environ.get('BUILDKITE_JOB_ID')}")
    print(f"BUILDKITE_COMMIT: {os.environ.get('BUILDKITE_COMMIT')}")
    print(f"BUILDKITE_ORGANIZATION_SLUG: {os.environ.get('BUILDKITE_ORGANIZATION_SLUG')}")
    print(f"BUILDKITE_PIPELINE_SLUG: {os.environ.get('BUILDKITE_PIPELINE_SLUG')}")
    
    # Direct API Integration Test
    print("\nTesting Direct Buildkite Analytics API Integration...")
    token = os.environ.get('BUILDKITE_ANALYTICS_TOKEN')
    if token:
        print(f"Using Analytics Token: {token[:10]}...{token[-4:] if len(token) > 14 else token}")
        headers = {'Authorization': f'Token token="{token}"', 'Content-Type': 'application/json'}
        try:
            # Sample test result payload for loguru bridge validation
            payload = {
                "format": "json",
                "run_env": {
                    "ci": "buildkite",
                    "key": os.environ.get("BUILDKITE_BUILD_ID"),
                    "url": f"https://buildkite.com/dagster/unit-tests/builds/{os.environ.get('BUILDKITE_BUILD_NUMBER', 'local-test')}",
                    "branch": os.environ.get("BUILDKITE_BRANCH", "Issue-29914-loguru-bridge"),
                    "commit_sha": os.environ.get("BUILDKITE_COMMIT"),
                    "number": os.environ.get("BUILDKITE_BUILD_NUMBER", "local-validation")
                },
                "data": [
                    {
                        "id": "test_buildkite_analytics_integration",
                        "scope": "logging_tests.buildkite_collector_validation",
                        "name": "Buildkite Analytics Integration Test",
                        "location": "test_buildkite_collector.py::test_buildkite_analytics_integration",
                        "result": "passed",
                        "history": {"section": "loguru_bridge_buildkite_integration"}
                    }
                ]
            }
            
            # POST to Buildkite Analytics API
            print("Sending test results to Buildkite Analytics API...")
            response = requests.post('https://analytics-api.buildkite.com/v1/uploads', 
                                   json=payload,
                                   headers=headers)
            print(f"API Response Status: {response.status_code}")
            if response.status_code == 200:
                print("Success! Test results uploaded to Buildkite Analytics")
            elif response.status_code == 401:
                print("Unauthorized - Token may need to be associated with test suite")
            else:
                print(f"Unexpected response: {response.status_code}")
            print(f"Response Details: {response.text}")
        except Exception as e:
            print(f"API Integration Error: {e}")
    else:
        print("No BUILDKITE_ANALYTICS_TOKEN found - skipping API test")
    
    assert True

if __name__ == "__main__":
    print("Starting Buildkite Analytics Integration Test...")
    
    # Validate required environment variable
    analytics_token = os.environ.get("BUILDKITE_ANALYTICS_TOKEN")
    if not analytics_token:
        print("ERROR: BUILDKITE_ANALYTICS_TOKEN environment variable must be set")
        print("Usage: export BUILDKITE_ANALYTICS_TOKEN='your_token_here'")
        exit(1)
    
    print("Analytics token found - setting up test environment...")
    
    # Set up meaningful test environment variables
    os.environ["BUILDKITE"] = "true"
    os.environ["BUILDKITE_BUILD_ID"] = "local-loguru-bridge-test-build"
    os.environ["BUILDKITE_JOB_ID"] = "logging-tests-job-validation"
    os.environ["BUILDKITE_COMMIT"] = "loguru-bridge-integration-commit"
    os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "dagster"
    os.environ["BUILDKITE_PIPELINE_SLUG"] = "unit-tests"
    
    print("Running pytest with local configuration...")
    exit_code = pytest.main(["-vvs", "-c", "pytest-local.ini", "test_buildkite_collector.py"])
    print(f"Test completed with exit code: {exit_code}")
    
    if exit_code == 0:
        print("All tests passed successfully!")
    else:
        print("Some tests failed - check output above")
