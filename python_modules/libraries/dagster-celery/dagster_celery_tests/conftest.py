import os

import docker
import pytest
from celery.contrib.testing import worker
from celery.contrib.testing.app import setup_default_app
from dagster_celery.make_app import make_app
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session")
def dagster_celery_app():
    app = make_app()
    with setup_default_app(app, use_trap=False):
        yield app


# pylint doesn't understand pytest fixtures
@pytest.fixture(scope="function")
def dagster_celery_worker(dagster_celery_app):  # pylint: disable=redefined-outer-name
    with worker.start_worker(dagster_celery_app, perform_ping_check=False) as w:
        yield w


@pytest.fixture(scope="session")
def dagster_docker_image():
    docker_image = test_project_docker_image()

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
