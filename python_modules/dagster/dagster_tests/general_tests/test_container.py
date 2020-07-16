def test_build_container(dagster_docker_image):
    assert "dagster-core-docker-buildkite" in dagster_docker_image
