import json
import os
import subprocess
import time
from contextlib import contextmanager

import requests
from dagster import file_relative_path

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@contextmanager
def docker_service_up(docker_compose_file):
    if IS_BUILDKITE:
        yield  # buildkite pipeline handles the service
        return

    try:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])
    except subprocess.CalledProcessError:
        pass

    build_process = subprocess.Popen([file_relative_path(docker_compose_file, "./build.sh")])
    build_process.wait()
    assert build_process.returncode == 0

    env_file = file_relative_path(docker_compose_file, ".env")

    up_process = subprocess.Popen(
        ["docker-compose", "--env-file", env_file, "-f", docker_compose_file, "up", "--no-start"]
    )
    up_process.wait()
    assert up_process.returncode == 0

    start_process = subprocess.Popen(
        ["docker-compose", "--env-file", env_file, "-f", docker_compose_file, "start"]
    )
    start_process.wait()
    assert start_process.returncode == 0

    try:
        yield
    finally:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])


PIPELINES_OR_ERROR_QUERY = """
{
    repositoriesOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryConnection {
            nodes {
                pipelines {
                    name
                }
            }
        }
    }
}
"""

RUN_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
      status
    }
  }
}
"""

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
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
    }
  }
}
"""


def test_deploy_docker():
    with docker_service_up(file_relative_path(__file__, "../from_source/docker-compose.yml")):
        # Wait for server to wake up

        start_time = time.time()

        dagit_host = os.environ.get("DEPLOY_DOCKER_DAGIT_HOST", "localhost")

        while True:
            if time.time() - start_time > 15:
                raise Exception("Timed out waiting for dagit server to be available")

            try:
                sanity_check = requests.get(
                    "http://{dagit_host}:3000/dagit_info".format(dagit_host=dagit_host)
                )
                assert "dagit" in sanity_check.text
                break
            except requests.exceptions.ConnectionError:
                pass

            time.sleep(1)

        res = requests.get(
            "http://{dagit_host}:3000/graphql?query={query_string}".format(
                dagit_host=dagit_host,
                query_string=PIPELINES_OR_ERROR_QUERY,
            )
        ).json()

        data = res.get("data")
        assert data

        repositoriesOrError = data.get("repositoriesOrError")
        assert repositoriesOrError

        nodes = repositoriesOrError.get("nodes")
        assert nodes

        assert nodes[0]["pipelines"][0]["name"] == "my_pipeline"

        variables = {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": "example_pipelines",
                    "repositoryName": "deploy_docker_repository",
                    "pipelineName": "my_pipeline",
                },
                "mode": "default",
            }
        }

        launch_res = requests.post(
            "http://{dagit_host}:3000/graphql?query={query_string}&variables={variables}".format(
                dagit_host=dagit_host,
                query_string=LAUNCH_PIPELINE_MUTATION,
                variables=json.dumps(variables),
            )
        ).json()

        assert (
            launch_res["data"]["launchPipelineExecution"]["__typename"]
            == "LaunchPipelineRunSuccess"
        )

        run = launch_res["data"]["launchPipelineExecution"]["run"]
        run_id = run["runId"]
        assert run["status"] == "QUEUED"

        start_time = time.time()

        while True:
            if time.time() - start_time > 60:
                raise Exception("Timed out waiting for launched run to complete")

            run_res = requests.get(
                "http://{dagit_host}:3000/graphql?query={query_string}&variables={variables}".format(
                    dagit_host=dagit_host,
                    query_string=RUN_QUERY,
                    variables=json.dumps({"runId": run_id}),
                )
            ).json()

            status = run_res["data"]["pipelineRunOrError"]["status"]
            assert status and status != "FAILED"

            if status == "SUCCESS":
                break

            time.sleep(1)
