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

LOCATION_ENTRY_QUERY = """
query($name: String!) {
  workspaceLocationEntryOrError(name: $name) {
    __typename
    ... on WorkspaceLocationEntry {
      name
      loadStatus
      locationOrLoadError {
        __typename
        ... on PythonError {
          message
        }
      }
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
    # successfully loaded its gRPC server as a code location. In dagster,
    # CodeLocationLoadStatus is a two-value enum (LOADING / LOADED) where
    # LOADED means "finished loading (may be an error)" — _load_location
    # always returns LOADED, even when the load attempt raised and the entry's
    # code_location is None. Polling loadStatus alone races the watch-thread
    # reload triggered by the first LOCATION_UPDATED event from the gRPC
    # server, and the first test fails with PipelineNotFoundError.
    #
    # Use workspaceLocationEntryOrError per location and require
    # locationOrLoadError to be a RepositoryLocation (not a PythonError) so
    # callers know the workspace actually has the location's repositories.
    expected = list(expected_location_names)
    start = time.time()
    last_states: dict[str, str] = {}
    while time.time() - start < timeout:
        states: dict[str, str] = {}
        for name in expected:
            try:
                result = _execute_query_over_graphql(
                    webserver_url,
                    LOCATION_ENTRY_QUERY,
                    variables=json.dumps({"name": name}),
                )
                entry = (result.get("data") or {}).get("workspaceLocationEntryOrError")
                if not entry or entry.get("__typename") != "WorkspaceLocationEntry":
                    states[name] = "MISSING"
                    continue
                inner = entry.get("locationOrLoadError")
                if entry.get("loadStatus") != "LOADED" or inner is None:
                    states[name] = "LOADING"
                elif inner.get("__typename") == "RepositoryLocation":
                    states[name] = "LOADED"
                else:
                    message = (inner.get("message") or "").splitlines()[0][:200]
                    states[name] = f"LOAD_ERROR: {message}"
            except Exception as e:
                states[name] = f"POLL_ERROR: {e}"

        last_states = states
        if all(s == "LOADED" for s in states.values()):
            print(f"Code locations loaded: {sorted(expected)}")
            return
        time.sleep(1)

    raise Exception(
        f"Timed out after {timeout}s waiting for code locations {sorted(expected)} "
        f"to load successfully. Last states: {last_states}"
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
