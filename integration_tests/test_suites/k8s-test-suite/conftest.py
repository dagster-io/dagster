# pylint: disable=unused-import
import os
import tempfile

import docker
import kubernetes
import pytest
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s_test_infra.cluster import (
    dagster_instance_for_k8s_run_launcher,
    define_cluster_provider_fixture,
    helm_postgres_url_for_k8s_run_launcher,
)
from dagster_k8s_test_infra.helm import (
    TEST_AWS_CONFIGMAP_NAME,
    TEST_IMAGE_PULL_SECRET_NAME,
    TEST_SECRET_NAME,
    TEST_VOLUME_CONFIGMAP_NAME,
)
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import build_and_tag_test_image, get_test_project_docker_image

from dagster.core.instance import DagsterInstance

pytest_plugins = ["dagster_k8s_test_infra.helm"]

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session", autouse=True)
def dagster_home():
    old_env = os.getenv("DAGSTER_HOME")
    os.environ["DAGSTER_HOME"] = "/opt/dagster/dagster_home"
    yield
    if old_env is not None:
        os.environ["DAGSTER_HOME"] = old_env


cluster_provider = define_cluster_provider_fixture(
    additional_kind_images=[
        "docker.io/busybox",
        "docker.io/bitnami/rabbitmq",
        "docker.io/bitnami/postgresql",
    ]
)


@pytest.yield_fixture
def schedule_tempdir():
    with tempfile.TemporaryDirectory() as tempdir:
        yield tempdir


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
