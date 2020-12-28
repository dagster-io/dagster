import pytest
from dagster import seven


@pytest.mark.skipif(seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_build_container(dagster_docker_image):
    assert "buildkite-test-image-core" in dagster_docker_image


@pytest.mark.skipif(seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_run_grpc_server_in_container(grpc_port, grpc_host):
    assert grpc_host
    assert grpc_port == 8090
