import pytest
from contextlib import contextmanager
from dagster import file_relative_path
from dagster_graphql import DagsterGraphQLClient
import subprocess

pytest_plugins = ["dagster_test.fixtures"]

# pylint: disable=redefined-outer-name
RELEASE_TEST_MAP = {
    "dagit__0.12.0": ["0.12.0", "current_branch"],
    "user_code__0.12.0": ["current_branch", "0.12.0"],
}


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
    dagit_version = release_test_map["dagit"]
    user_code_version = release_test_map["user_code"]

    with docker_service_up(file_relative_path(__file__, "./dagit_service/docker-compose.yml")):
        result = retrying_requests.get("http://127.0.0.1:3000/dagit_info")
        assert result.json().get("dagit_version")
        yield DagsterGraphQLClient("127.0.0.1", port_number=3000)


def test_backcompat_deploy(graphql_client):
    assert graphql_client
