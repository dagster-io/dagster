import os
import subprocess
import time
from contextlib import contextmanager

import pytest
from dagster import file_relative_path
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster_graphql import DagsterGraphQLClient

MAX_TIMEOUT_SECONDS = 20
IS_BUILDKITE = os.getenv("BUILDKITE") is not None

pytest_plugins = ["dagster_test.fixtures"]

# pylint: disable=redefined-outer-name
RELEASE_TEST_MAP = {
    "dagit__0.12.8": ["0.12.8", "current_branch"],
    "user_code__0.12.8": ["current_branch", "0.12.8"],
}


def assert_run_success(client, run_id: int):
    start_time = time.time()
    while True:
        if time.time() - start_time > MAX_TIMEOUT_SECONDS:
            raise Exception("Timed out waiting for launched run to complete")

        status = client.get_run_status(run_id)
        assert status and status != PipelineRunStatus.FAILURE
        if status == PipelineRunStatus.SUCCESS:
            break

        time.sleep(1)


@pytest.fixture(
    params=[
        pytest.param(value, marks=getattr(pytest.mark, key), id=key)
        for key, value in RELEASE_TEST_MAP.items()
    ],
)
def release_test_map(request):
    dagit_version = request.param[0]
    user_code_version = request.param[1]

    return {"dagit": dagit_version, "user_code": user_code_version}


@contextmanager
def docker_service_up(docker_compose_file, build_args=None):
    if IS_BUILDKITE:
        yield  # buildkite pipeline handles the service
        return

    try:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])
    except subprocess.CalledProcessError:
        pass

    build_process = subprocess.Popen(
        [file_relative_path(docker_compose_file, "./build.sh")] + (build_args if build_args else [])
    )
    build_process.wait()
    assert build_process.returncode == 0

    up_process = subprocess.Popen(["docker-compose", "-f", docker_compose_file, "up", "--no-start"])
    up_process.wait()
    assert up_process.returncode == 0

    start_process = subprocess.Popen(["docker-compose", "-f", docker_compose_file, "start"])
    start_process.wait()
    assert start_process.returncode == 0

    try:
        yield
    finally:
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "stop"])
        subprocess.check_output(["docker-compose", "-f", docker_compose_file, "rm", "-f"])


@pytest.fixture
def graphql_client(release_test_map, retrying_requests):
    dagit_host = os.environ.get("BACKCOMPAT_TESTS_DAGIT_HOST", "localhost")

    dagit_version = release_test_map["dagit"]
    user_code_version = release_test_map["user_code"]

    if dagit_version == "current_branch":
        os.environ["DAGIT_DOCKERFILE"] = "./Dockerfile_dagit_source"
    else:
        os.environ["DAGIT_DOCKERFILE"] = "./Dockerfile_dagit_release"

    if user_code_version == "current_branch":
        os.environ["USER_CODE_DOCKERFILE"] = "./Dockerfile_grpc_source"
    else:
        os.environ["USER_CODE_DOCKERFILE"] = "./Dockerfile_grpc_release"

    with docker_service_up(
        file_relative_path(__file__, "./dagit_service/docker-compose.yml"),
        build_args=[dagit_version, user_code_version],
    ):
        result = retrying_requests.get(f"http://{dagit_host}:3000/dagit_info")
        assert result.json().get("dagit_version")
        yield DagsterGraphQLClient(dagit_host, port_number=3000)


def test_backcompat_deployed_pipeline(graphql_client):
    assert_runs_and_exists(graphql_client, "the_pipeline")


def test_backcompat_deployed_job(graphql_client):
    assert_runs_and_exists(graphql_client, "the_job")


def assert_runs_and_exists(client, name):
    run_id = client.submit_pipeline_execution(pipeline_name=name, mode="default", run_config={})
    assert_run_success(client, run_id)

    locations = (
        client._get_repo_locations_and_names_with_pipeline(  # pylint: disable=protected-access
            pipeline_name=name
        )
    )
    assert len(locations) == 1
    assert locations[0].pipeline_name == name
