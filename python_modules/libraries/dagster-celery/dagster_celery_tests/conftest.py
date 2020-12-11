import os
import subprocess
import time

import docker
import pytest
from celery.contrib.testing import worker
from celery.contrib.testing.app import setup_default_app
from dagster import file_relative_path
from dagster.core.test_utils import environ
from dagster_celery.make_app import make_app
from dagster_celery.tasks import create_task
from dagster_test.test_project import build_and_tag_test_image, get_test_project_docker_image

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
    except Exception:  # pylint: disable=broad-except
        pass

    subprocess.check_output(["docker-compose", "-f", docker_compose_file, "up", "-d", service_name])

    print("Waiting for rabbitmq to be ready...")  # pylint: disable=print-call
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
        except Exception:  # pylint: disable=broad-except
            pass


@pytest.fixture(scope="session")
def dagster_celery_app(rabbitmq):  # pylint: disable=redefined-outer-name, unused-argument
    app = make_app()
    execute_plan = create_task(app)  # pylint: disable=unused-variable

    with setup_default_app(app, use_trap=False):
        yield app


# pylint doesn't understand pytest fixtures
@pytest.fixture(scope="function")
def dagster_celery_worker(dagster_celery_app):  # pylint: disable=redefined-outer-name
    with worker.start_worker(dagster_celery_app, perform_ping_check=False) as w:
        yield w


@pytest.fixture(scope="session")
def dagster_docker_image():
    docker_image = get_test_project_docker_image()

    if not IS_BUILDKITE:
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(  # pylint: disable=print-call
                "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                "docker rmi {image}".format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            build_and_tag_test_image(docker_image)

    return docker_image
