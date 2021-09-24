# pylint: disable=redefined-outer-name
import os
import subprocess

import pytest
import yaml

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture
def other_docker_compose_yml(tmpdir):
    original = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
    with open(original, "r") as f:
        docker_compose_yml = yaml.safe_load(f)

    docker_compose_yml["services"]["server"]["container_name"] = "other_server"

    other = tmpdir / "docker-compose.yml"
    other.write(yaml.safe_dump(docker_compose_yml))

    yield other


def test_docker_compose(docker_compose, retrying_requests):
    assert retrying_requests.get(f"http://{docker_compose['server']}:8000").ok


def test_docker_compose_cm_from_test_directory(docker_compose_cm, retrying_requests):
    with docker_compose_cm() as docker_compose:
        assert retrying_requests.get(f"http://{docker_compose['server']}:8000").ok


def test_docker_compose_cm_from_cwd(other_docker_compose_yml, docker_compose_cm, retrying_requests):
    with other_docker_compose_yml.dirpath().as_cwd(), docker_compose_cm() as docker_compose:
        assert retrying_requests.get(f"http://{docker_compose['other_server']}:8000").ok


def test_docker_compose_cm_with_yml(other_docker_compose_yml, docker_compose_cm, retrying_requests):
    with docker_compose_cm(docker_compose_yml=other_docker_compose_yml) as docker_compose:
        assert retrying_requests.get(f"http://{docker_compose['other_server']}:8000").ok


def test_docker_compose_cm_with_network(request, docker_compose_cm, retrying_requests):
    with docker_compose_cm(
        docker_compose_yml=os.path.join(
            os.path.dirname(request.fspath), "networked-docker-compose.yml"
        ),
        network_name="network",
    ) as docker_compose:
        assert "network" in subprocess.check_output(["docker", "network", "ls"]).decode()
        assert retrying_requests.get(f"http://{docker_compose['server']}:8000").ok


def test_docker_compose_cm_single_service(request, docker_compose_cm, retrying_requests):
    with docker_compose_cm(
        docker_compose_yml=os.path.join(
            os.path.dirname(request.fspath), "multi-service-docker-compose.yml"
        ),
        service="server2",
    ) as docker_compose:
        assert not docker_compose.get("server1")
        assert retrying_requests.get(f"http://{docker_compose['server2']}:8001").ok
