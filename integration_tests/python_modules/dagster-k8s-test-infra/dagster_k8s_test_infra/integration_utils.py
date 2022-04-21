# pylint: disable=print-call
import json
import os
import random
import subprocess

import requests

from dagster.utils import merge_dicts

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
    """Uses distutils to look for an executable, mimicking unix which"""
    from distutils import spawn  # pylint: disable=no-name-in-module

    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def get_test_namespace():
    namespace_suffix = hex(random.randint(0, 16**6))[2:]
    return "dagster-test-%s" % namespace_suffix


def within_docker():
    """detect if we're running inside of a docker container

    from: https://stackoverflow.com/a/48710609/11295366
    """
    cgroup_path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(cgroup_path)
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


def _execute_query_over_graphql(dagit_url, query, variables):
    return requests.post(
        f"{dagit_url}/graphql",
        headers={"Content-type": "application/json"},
        json=merge_dicts(
            {
                "query": query,
            },
            {"variables": variables} if variables else {},
        ),
    ).json()


def launch_run_over_graphql(
    dagit_url,
    run_config,
    pipeline_name,
    repository_name="demo_execution_repo",
    repository_location_name="user-code-deployment-1",
    mode="default",
    solid_selection=None,
):
    variables = json.dumps(
        {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": repository_location_name,
                    "repositoryName": repository_name,
                    "pipelineName": pipeline_name,
                    "solidSelection": solid_selection,
                },
                "runConfigData": run_config,
                "mode": mode,
            }
        }
    )

    result = _execute_query_over_graphql(dagit_url, LAUNCH_PIPELINE_MUTATION, variables)

    print("Launch pipeline result: {}".format(str(result)))

    assert (
        "data" in result
        and result["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    )

    return result["data"]["launchPipelineExecution"]["run"]["runId"]


def can_terminate_run_over_graphql(
    dagit_url,
    run_id,
) -> bool:
    variables = json.dumps({"runId": run_id})
    result = _execute_query_over_graphql(dagit_url, CAN_TERMINATE_RUN_QUERY, variables)
    print("Can terminate result: {}".format(str(result)))
    assert "data" in result and result["data"]["runOrError"]["__typename"] == "Run"
    return result["data"]["runOrError"]["canTerminate"]


def terminate_run_over_graphql(dagit_url, run_id):
    variables = json.dumps({"runId": run_id})
    result = _execute_query_over_graphql(dagit_url, TERMINATE_RUN_MUTATION, variables)
    print("Terminate result: {}".format(str(result)))
    assert (
        "data" in result and result["data"]["terminateRun"]["__typename"] == "TerminateRunSuccess"
    )
