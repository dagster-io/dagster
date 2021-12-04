# pylint: disable=unused-import
import os

import docker
import pytest
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher
from dagster_k8s_test_infra.helm import TEST_AWS_CONFIGMAP_NAME
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import build_and_tag_test_image, get_test_project_docker_image

from dagster_k8s_test_infra.cluster import (  # isort:skip
    dagster_instance,
    dagster_instance_for_user_deployments_subchart_disabled,
    dagster_instance_for_daemon,
    define_cluster_provider_fixture,
    helm_postgres_url,
    helm_postgres_url_for_user_deployments_subchart_disabled,
    helm_postgres_url_for_daemon,
)

pytest_plugins = ["dagster_k8s_test_infra.helm"]

cluster_provider = define_cluster_provider_fixture()

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


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


# See: https://stackoverflow.com/a/31526934/324449
def pytest_addoption(parser):
    # We catch the ValueError to support cases where we are loading multiple test suites, e.g., in
    # the VSCode test explorer. When pytest tries to add an option twice, we get, e.g.
    #
    #    ValueError: option names {'--cluster-provider'} already added

    # Use kind or some other cluster provider?
    try:
        parser.addoption("--cluster-provider", action="store", default="kind")
    except ValueError:
        pass

    # Specify an existing kind cluster name to use
    try:
        parser.addoption("--kind-cluster", action="store")
    except ValueError:
        pass

    # Keep resources around after tests are done
    try:
        parser.addoption("--no-cleanup", action="store_true", default=False)
    except ValueError:
        pass

    # Use existing Helm chart/namespace
    try:
        parser.addoption("--existing-helm-namespace", action="store")
    except ValueError:
        pass
