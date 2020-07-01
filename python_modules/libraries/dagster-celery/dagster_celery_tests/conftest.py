import os
import sys

import docker
import pytest
import six
from celery.contrib.testing import worker
from celery.contrib.testing.app import setup_default_app
from dagster_celery.make_app import make_app
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

from dagster.utils import git_repository_root

try:
    sys.path.append(
        os.path.join(git_repository_root(), 'python_modules', 'libraries', 'dagster-k8s')
    )
    # pylint: disable=unused-import
    from dagster_k8s_tests.integration_tests.cluster import define_cluster_provider_fixture
    from dagster_k8s_tests.integration_tests.helm import helm_namespace
except ImportError as import_exc:
    six.raise_from(
        Exception(
            'Expected to find dagster-k8s in python_modules/libraries/dagster-k8s, please run these'
            ' tests from a clean checkout of the dagster repository'
        ),
        import_exc,
    )

IS_BUILDKITE = os.getenv('BUILDKITE') is not None


@pytest.fixture(scope='session')
def dagster_celery_app():
    app = make_app()
    with setup_default_app(app, use_trap=False):
        yield app


# pylint doesn't understand pytest fixtures
@pytest.fixture(scope='function')
def dagster_celery_worker(dagster_celery_app):  # pylint: disable=redefined-outer-name
    with worker.start_worker(dagster_celery_app, perform_ping_check=False) as w:
        yield w


@pytest.fixture(scope='session')
def dagster_docker_image():
    docker_image = test_project_docker_image()

    if not IS_BUILDKITE:
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(
                'Found existing image tagged {image}, skipping image build. To rebuild, first run: '
                'docker rmi {image}'.format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            build_and_tag_test_image(docker_image)

    return docker_image


cluster_provider = define_cluster_provider_fixture()
