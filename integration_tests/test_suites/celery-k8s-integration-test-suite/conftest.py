# pylint: disable=unused-import
import os

import docker
import pytest
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher
from dagster_k8s_test_infra.helm import (
    helm_namespace,
    helm_namespace_for_run_coordinator,
    helm_namespace_for_user_deployments,
)
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

from dagster_k8s_test_infra.cluster import (  # isort:skip
    dagster_instance,
    dagster_instance_for_user_deployments,
    dagster_instance_for_run_coordinator,
    define_cluster_provider_fixture,
)

cluster_provider = define_cluster_provider_fixture()

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


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


@pytest.fixture(scope="session")
def run_launcher(
    cluster_provider, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument
    return CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=cluster_provider.kubeconfig_file,
    )


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
