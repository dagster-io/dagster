import pytest

from dagster import _seven


@pytest.mark.skipif(_seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_build_container(dagster_docker_image):
    assert "test-project-core" in dagster_docker_image


@pytest.mark.skipif(_seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_run_grpc_server_in_container(grpc_port, grpc_host):
    assert grpc_host
    assert grpc_port == 8090
