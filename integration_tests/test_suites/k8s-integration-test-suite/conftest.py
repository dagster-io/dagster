# pylint: disable=unused-import
import os

import docker
import kubernetes
import pytest
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.scheduler import K8sScheduler
from dagster_k8s_test_infra.cluster import (
    dagster_instance,
    dagster_instance_with_k8s_scheduler,
    define_cluster_provider_fixture,
)
from dagster_k8s_test_infra.helm import helm_namespace
from dagster_k8s_test_infra.integration_utils import image_pull_policy
from dagster_test.test_project import build_and_tag_test_image, test_project_docker_image

from dagster import seven
from dagster.core.instance import DagsterInstance

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session", autouse=True)
def dagster_home():
    old_env = os.getenv("DAGSTER_HOME")
    os.environ["DAGSTER_HOME"] = "/opt/dagster/dagster_home"
    yield
    if old_env is not None:
        os.environ["DAGSTER_HOME"] = old_env


cluster_provider = define_cluster_provider_fixture(
    additional_kind_images=["docker.io/bitnami/rabbitmq", "docker.io/bitnami/postgresql"]
)


@pytest.yield_fixture
def schedule_tempdir():
    with seven.TemporaryDirectory() as tempdir:
        yield tempdir


@pytest.fixture
def k8s_scheduler(
    cluster_provider, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument
    return K8sScheduler(
        scheduler_namespace=helm_namespace,
        image_pull_secrets=[{"name": "element-dev-key"}],
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image=test_project_docker_image(),
        load_incluster_config=False,
        kubeconfig_file=cluster_provider.kubeconfig_file,
        image_pull_policy=image_pull_policy(),
        env_config_maps=["dagster-pipeline-env", "test-env-configmap"],
        env_secrets=["test-env-secret"],
    )


@pytest.fixture(scope="function")
def restore_k8s_cron_tab(helm_namespace):  # pylint: disable=redefined-outer-name
    kube_api = kubernetes.client.BatchV1beta1Api()
    # Doubly make sure CronJobs are deleted pre-test and post-test
    kube_api.delete_collection_namespaced_cron_job(namespace=helm_namespace)
    yield
    kube_api.delete_collection_namespaced_cron_job(namespace=helm_namespace)


@pytest.fixture(scope="session")
def run_launcher(
    cluster_provider, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument

    return K8sRunLauncher(
        image_pull_secrets=[{"name": "element-dev-key"}],
        service_account_name="dagit-admin",
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        job_image=test_project_docker_image(),
        load_incluster_config=False,
        kubeconfig_file=cluster_provider.kubeconfig_file,
        image_pull_policy=image_pull_policy(),
        job_namespace=helm_namespace,
        env_config_maps=["dagster-pipeline-env", "test-env-configmap"],
        env_secrets=["test-env-secret"],
    )


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
