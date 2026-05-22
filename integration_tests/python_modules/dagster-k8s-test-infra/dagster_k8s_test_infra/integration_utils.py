# ruff: noqa: T201
import json
import os
import random
import subprocess
import time
from collections.abc import Mapping, Sequence
from typing import Any

import requests
from dagster._utils.merger import merge_dicts

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def image_pull_policy():
    # This is because when running local tests, we need to load the image into the kind cluster (and
    # then not attempt to pull it) because we don't want to require credentials for a private
    # registry / pollute the private registry / set up and network a local registry as a condition
    # of running tests
    if IS_BUILDKITE:
        return "Always"
    else:
        return "IfNotPresent"


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode("utf-8")
        raise Exception(output) from exc


def which_(exe):
    """Uses distutils to look for an executable, mimicking unix which."""
    from distutils import spawn

    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def get_test_namespace(prefix="dagster-test"):
    namespace_suffix = hex(random.randint(0, 16**6))[2:]
    return f"{prefix}-{namespace_suffix}"


def within_docker():
    """Detect if we're running inside of a docker container.

    from: https://stackoverflow.com/a/48710609/11295366
    """
    cgroup_path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or (
        os.path.isfile(cgroup_path)
        and any("docker" in line for line in open(cgroup_path, encoding="utf8"))
    )


LAUNCH_PIPELINE_MUTATION = """
mutation($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    __typename
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        status
      }
    }
    ... on PresetNotFoundError {
      preset
      message
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
    }
    ... on ConflictingExecutionParamsError {
      message
    }
  }
}
"""

CAN_TERMINATE_RUN_QUERY = """
query($runId: ID!) {
  runOrError(runId: $runId) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on Run {
      canTerminate
    }
  }
}
"""

LOCATION_STATUSES_QUERY = """
query {
  locationStatusesOrError {
    __typename
    ... on WorkspaceLocationStatusEntries {
      entries {
        name
        loadStatus
      }
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""

TERMINATE_RUN_MUTATION = """
mutation($runId: String!, $terminatePolicy: TerminateRunPolicy) {
  terminateRun(runId: $runId, terminatePolicy:$terminatePolicy){
    __typename
    ... on TerminateRunSuccess{
      run {
        runId
      }
    }
    ... on TerminateRunFailure {
      run {
        runId
      }
      message
    }
    ... on RunNotFoundError {
      runId
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""


def _execute_query_over_graphql(webserver_url, query, variables):
    return requests.post(
        f"{webserver_url}/graphql",
        headers={"Content-type": "application/json"},
        json=merge_dicts(
            {
                "query": query,
            },
            {"variables": variables} if variables else {},
        ),
    ).json()


def wait_for_workspace_loaded(
    webserver_url: str,
    expected_location_names: Sequence[str],
    timeout: int = 180,
) -> None:
    # Pod-readiness of a user-code-deployment doesn't imply the webserver has
    # finished polling its gRPC server and registered it as a code location.
    # The first test in a fresh suite races this gap and fails with
    # PipelineNotFoundError. Block here until every expected location reports
    # LOADED so callers can launch runs immediately.
    expected = set(expected_location_names)
    start = time.time()
    last_status: Mapping[str, str] = {}
    while time.time() - start < timeout:
        try:
            result = _execute_query_over_graphql(
                webserver_url, LOCATION_STATUSES_QUERY, variables=None
            )
            payload = result.get("data", {}).get("locationStatusesOrError", {})
            if payload.get("__typename") == "WorkspaceLocationStatusEntries":
                last_status = {e["name"]: e["loadStatus"] for e in payload["entries"]}
                if expected.issubset(last_status) and all(
                    last_status[name] == "LOADED" for name in expected
                ):
                    print(f"Code locations loaded: {sorted(expected)}")
                    return
        except Exception as e:
            print(f"Polling workspace load status failed (retrying): {e}")
        time.sleep(1)
    raise Exception(
        f"Timed out after {timeout}s waiting for code locations {sorted(expected)} to load. "
        f"Last status: {last_status}"
    )


def launch_run_over_graphql(
    webserver_url: str,
    run_config: Mapping[str, Any],
    job_name: str,
    repository_name: str = "demo_execution_repo",
    code_location_name: str = "user-code-deployment-1",
    op_selection: Sequence[str] | None = None,
    tags: Mapping[str, str] | None = None,
) -> str:
    tags = tags or {}
    variables = json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": code_location_name,
                    "repositoryName": repository_name,
                    "pipelineName": job_name,
                    "solidSelection": op_selection,
                },
                "runConfigData": run_config,
                "executionMetadata": {
                    "tags": [{"key": key, "value": value} for key, value in tags.items()]
                },
            }
        }
    )

    result = _execute_query_over_graphql(webserver_url, LAUNCH_PIPELINE_MUTATION, variables)

    print(f"Launch pipeline result: {result}")

    assert (
        "data" in result
        and result["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    )

    return result["data"]["launchPipelineExecution"]["run"]["runId"]


def can_terminate_run_over_graphql(
    webserver_url,
    run_id,
) -> bool:
    variables = json.dumps({"runId": run_id})
    result = _execute_query_over_graphql(webserver_url, CAN_TERMINATE_RUN_QUERY, variables)
    print(f"Can terminate result: {result}")
    assert "data" in result and result["data"]["runOrError"]["__typename"] == "Run"
    return result["data"]["runOrError"]["canTerminate"]


def terminate_run_over_graphql(webserver_url, run_id):
    variables = json.dumps({"runId": run_id})
    result = _execute_query_over_graphql(webserver_url, TERMINATE_RUN_MUTATION, variables)
    print(f"Terminate result: {result}")
    assert (
        "data" in result and result["data"]["terminateRun"]["__typename"] == "TerminateRunSuccess"
    )
