# pylint: disable=redefined-outer-name
import os
import subprocess

import pytest
import yaml
from dagster_test.fixtures.docker_compose import (
    connect_container_to_network,
    disconnect_container_from_network,
    network_name_from_yml,
)

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture(autouse=True)
def environ(monkeypatch, test_id):
    monkeypatch.setenv("TEST_VOLUME", test_id)


@pytest.fixture
def other_docker_compose_yml(tmpdir):
    original = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
    with open(original, "r", encoding="utf8") as f:
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


def test_docker_compose_cm_destroys_volumes(docker_compose_cm, test_id):
    with docker_compose_cm():
        assert subprocess.check_output(["docker", "volume", "inspect", test_id])
    with pytest.raises(Exception):
        subprocess.check_output(["docker", "volume", "inspect", test_id])


def test_connect_container_to_network(docker_compose_cm, other_docker_compose_yml, caplog):
    caplog.set_level("INFO")

    with docker_compose_cm(docker_compose_yml=other_docker_compose_yml) as docker_compose:
        container = next(iter(docker_compose))
        network = network_name_from_yml(other_docker_compose_yml)
        disconnect_container_from_network(container=container, network=network)
        # Connecting multiple times is idempotent
        connect_container_to_network(container=container, network=network)
        assert f"Connected {container} to network {network}." in caplog.text
        connect_container_to_network(container=container, network=network)
        assert f"Unable to connect {container} to network {network}." in caplog.text


def test_disconnect_container_from_network(docker_compose_cm, other_docker_compose_yml, caplog):
    caplog.set_level("INFO")

    with docker_compose_cm(docker_compose_yml=other_docker_compose_yml) as docker_compose:
        container = next(iter(docker_compose))
        network = network_name_from_yml(other_docker_compose_yml)
        # Disconnecting multiple times is idempotent
        disconnect_container_from_network(container=container, network=network)
        assert f"Disconnected {container} from network {network}." in caplog.text
        disconnect_container_from_network(container=container, network=network)
        assert f"Unable to disconnect {container} from network {network}." in caplog.text
