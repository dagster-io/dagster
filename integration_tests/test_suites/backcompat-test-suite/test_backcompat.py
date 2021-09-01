import pytest
import requests
import time
from contextlib import contextmanager
from dagster import file_relative_path
from dagster_graphql import DagsterGraphQLClient
import subprocess

pytest_plugins = ["dagster_test.fixtures"]

# pylint: disable=redefined-outer-name
RELEASE_TEST_MAP = {"master": ["master", "master"], "0.12.x": ["0.12.5", "master"]}


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


# TODO: switch to using dagster_test.fixtures
@contextmanager
def docker_service_up(docker_compose_file, build_args=None):

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
def graphql_client(retrying_requests):
    with docker_service_up(file_relative_path(__file__, "./dagit_service/docker-compose.yml")):
        result = retrying_requests.get("http://127.0.0.1:3000/dagit_info")
        assert result.json().get("dagit_version")
        yield DagsterGraphQLClient("127.0.0.1", port_number=3000)


def test_backcompat_deploy(release_test_map, graphql_client):
    assert release_test_map, graphql_client
