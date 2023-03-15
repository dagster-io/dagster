import os
import subprocess
import tempfile
import time

import docker
import pytest
from dagster import file_relative_path
from dagster._core.test_utils import environ, instance_for_test
from dagster_test.test_project import build_and_tag_test_image, get_test_project_docker_image

from .utils import start_celery_worker

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session")
def rabbitmq():  # pylint: disable=redefined-outer-name
    if IS_BUILDKITE:
        # Set the enviornment variable that celery uses in the start_worker() test function
        # to find the broker host
        with environ({"TEST_BROKER": os.getenv("DAGSTER_CELERY_BROKER_HOST", "localhost")}):
            yield
        return

    docker_compose_file = file_relative_path(__file__, "../docker-compose.yaml")

    service_name = "test-rabbitmq"

    try:
        subprocess.check_output(
            ["docker-compose", "-f", docker_compose_file, "stop", service_name],
        )
        subprocess.check_output(
            ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name],
        )
    except Exception:
        pass

    subprocess.check_output(["docker-compose", "-f", docker_compose_file, "up", "-d", service_name])

    print("Waiting for rabbitmq to be ready...")  # noqa: T201
    while True:
        logs = str(subprocess.check_output(["docker", "logs", service_name]))
        if "started TCP listener on [::]:5672" in logs:
            break
        time.sleep(1)

    try:
        yield
    finally:
        try:
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "stop", service_name]
            )
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name]
            )
        except Exception:
            pass


@pytest.fixture(scope="function")
def tempdir():
    with tempfile.TemporaryDirectory() as the_dir:
        yield the_dir


@pytest.fixture(scope="function")
def instance(tempdir):  # pylint: disable=redefined-outer-name
    with instance_for_test(temp_dir=tempdir) as test_instance:
        yield test_instance


@pytest.fixture(scope="function")
def dagster_celery_worker(
    rabbitmq, instance
):  # pylint: disable=redefined-outer-name, unused-argument
    with start_celery_worker():
        yield


@pytest.fixture(scope="session")
def dagster_docker_image():
    docker_image = get_test_project_docker_image()

    if not IS_BUILDKITE:
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(  # noqa: T201
                "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                "docker rmi {image}".format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            build_and_tag_test_image(docker_image)

    return docker_image
