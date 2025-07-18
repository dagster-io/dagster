import os
import pytest
import requests

def test_simple():
    print("Test is running!")
    print(f"BUILDKITE_ANALYTICS_TOKEN: {os.environ.get('BUILDKITE_ANALYTICS_TOKEN')}")
    print(f"BUILDKITE: {os.environ.get('BUILDKITE')}")
    print(f"BUILDKITE_BUILD_ID: {os.environ.get('BUILDKITE_BUILD_ID')}")
    print(f"BUILDKITE_JOB_ID: {os.environ.get('BUILDKITE_JOB_ID')}")
    print(f"BUILDKITE_COMMIT: {os.environ.get('BUILDKITE_COMMIT')}")
    print(f"BUILDKITE_ORGANIZATION_SLUG: {os.environ.get('BUILDKITE_ORGANIZATION_SLUG')}")
    print(f"BUILDKITE_PIPELINE_SLUG: {os.environ.get('BUILDKITE_PIPELINE_SLUG')}")
    
    # Test direct API call - with correct token format and method
    token = os.environ.get('BUILDKITE_ANALYTICS_TOKEN')
    if token:
        headers = {'Authorization': f'Token token="{token}"', 'Content-Type': 'application/json'}
        try:
            # Sample test result payload for upload
            payload = {
                "format": "json",
                "run_env": {
                    "ci": "buildkite",
                    "key": os.environ.get("BUILDKITE_BUILD_ID"),
                    "url": f"https://buildkite.com/dagster/unit-tests/builds/{os.environ.get('BUILDKITE_BUILD_NUMBER', '1')}",
                    "branch": os.environ.get("BUILDKITE_BRANCH", "Issue-29914"),
                    "commit_sha": os.environ.get("BUILDKITE_COMMIT"),
                    "number": os.environ.get("BUILDKITE_BUILD_NUMBER", "1916")
                },
                "data": [
                    {
                        "id": "test_simple",
                        "scope": "test_buildkite_collector.py",
                        "name": "test_simple",
                        "location": "test_buildkite_collector.py:3",
                        "result": "passed",
                        "history": {"section": "test_buildkite_collector.py"}
                    }
                ]
            }
            
            # POST to the uploads endpoint
            response = requests.post('https://analytics-api.buildkite.com/v1/uploads', 
                                   json=payload,
                                   headers=headers)
            print(f"Direct API test status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"API test error: {e}")
    
    assert True

if __name__ == "__main__":
    # Use existing environment variable or fail if not set
    analytics_token = os.environ["BUILDKITE_ANALYTICS_TOKEN"]
    os.environ["BUILDKITE"] = "true"
    os.environ["BUILDKITE_BUILD_ID"] = "01981ad1-a952-49a2-97c0-7715c68ed6e9"
    os.environ["BUILDKITE_JOB_ID"] = "01981ad1-a964-45d8-9df4-e85dde0d2654"
    os.environ["BUILDKITE_COMMIT"] = "8558d6fc2b0e5cf8c2012a936d674fb88cb9a5a3"
    os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "dagster"
    os.environ["BUILDKITE_PIPELINE_SLUG"] = "unit-tests"
    
    exit_code = pytest.main(["-vvs", "-c", "pytest-local.ini", "test_buildkite_collector.py"])
    print(f"Exit code: {exit_code}")
