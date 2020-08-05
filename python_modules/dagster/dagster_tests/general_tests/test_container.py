def test_build_container(dagster_docker_image):
    assert "dagster-core-docker-buildkite" in dagster_docker_image


def test_run_grpc_server_in_container(grpc_port, grpc_host):
    assert grpc_host
    assert grpc_port == 8090
