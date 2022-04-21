# pylint: disable=print-call
import os
import subprocess
import tempfile
import time
from collections import namedtuple
from contextlib import contextmanager

import docker
import kubernetes
import psycopg2
import pytest
from dagster_k8s.utils import wait_for_pod
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage, PostgresScheduleStorage
from dagster_test.test_project import build_and_tag_test_image, get_test_project_docker_image

from dagster import check
from dagster.cli.debug import export_run
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.instance.ref import InstanceRef
from dagster.core.run_coordinator import DefaultRunCoordinator, QueuedRunCoordinator
from dagster.core.scheduler import DagsterDaemonScheduler
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.test_utils import ExplodingRunLauncher, environ
from dagster.utils import find_free_port

from .integration_utils import IS_BUILDKITE, check_output

# How long to wait before giving up on trying to establish postgres port forwarding
PG_PORT_FORWARDING_TIMEOUT = 60  # 1 minute


class ClusterConfig(namedtuple("_ClusterConfig", "name kubeconfig_file")):
    """Used to represent a cluster, returned by the cluster_provider fixture below."""

    def __new__(cls, name, kubeconfig_file):
        return super(ClusterConfig, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            kubeconfig_file=check.str_param(kubeconfig_file, "kubeconfig_file"),
        )


def define_cluster_provider_fixture(additional_kind_images=None):
    @pytest.fixture(scope="session")
    def _cluster_provider(request):
        from .kind import kind_cluster, kind_load_images

        if IS_BUILDKITE:
            print("Installing ECR credentials...")
            check_output("aws ecr get-login --no-include-email --region us-west-2 | sh", shell=True)

        provider = request.config.getoption("--cluster-provider")

        # Use a kind cluster
        if provider == "kind":
            cluster_name = request.config.getoption("--kind-cluster")

            # Cluster will be deleted afterwards unless this is set.
            # This is to allow users to reuse an existing cluster in local test by running
            # `pytest --kind-cluster my-cluster --no-cleanup` -- this avoids the per-test run
            # overhead of cluster setup and teardown
            should_cleanup = True if IS_BUILDKITE else not request.config.getoption("--no-cleanup")

            with kind_cluster(cluster_name, should_cleanup=should_cleanup) as cluster_config:
                if not IS_BUILDKITE:
                    docker_image = get_test_project_docker_image()
                    try:
                        client = docker.from_env()
                        client.images.get(docker_image)
                        print(  # pylint: disable=print-call
                            "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                            "docker rmi {image}".format(image=docker_image)
                        )
                    except docker.errors.ImageNotFound:
                        build_and_tag_test_image(docker_image)
                    kind_load_images(
                        cluster_name=cluster_config.name,
                        local_dagster_test_image=docker_image,
                        additional_images=additional_kind_images,
                    )
                yield cluster_config

        # Use cluster from kubeconfig
        elif provider == "kubeconfig":
            kubeconfig_file = os.getenv("KUBECONFIG", os.path.expandvars("${HOME}/.kube/config"))
            kubernetes.config.load_kube_config(config_file=kubeconfig_file)
            yield ClusterConfig(name="from_system_kubeconfig", kubeconfig_file=kubeconfig_file)

        else:
            raise Exception("unknown cluster provider %s" % provider)

    return _cluster_provider


@contextmanager
def local_port_forward_postgres(namespace):
    print("Port-forwarding postgres")
    postgres_pod_name = (
        check_output(
            [
                "kubectl",
                "get",
                "pods",
                "--namespace",
                namespace,
                "-l",
                "app=postgresql,release=dagster",
                "-o",
                'jsonpath="{.items[0].metadata.name}"',
            ]
        )
        .decode("utf-8")
        .strip('"')
    )
    forward_port = find_free_port()

    wait_for_pod(postgres_pod_name, namespace=namespace)

    p = None
    try:
        p = subprocess.Popen(
            [
                "kubectl",
                "port-forward",
                "--namespace",
                namespace,
                postgres_pod_name,
                "{forward_port}:5432".format(forward_port=forward_port),
            ],
            # Squelch the verbose "Handling connection for..." messages
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        # Validate port forwarding works
        start = time.time()

        while True:
            if time.time() - start > PG_PORT_FORWARDING_TIMEOUT:
                raise Exception("Timed out while waiting for postgres port forwarding")

            print(
                "Waiting for port forwarding from k8s pod %s:5432 to localhost:%d to be"
                " available..." % (postgres_pod_name, forward_port)
            )
            try:
                conn = psycopg2.connect(
                    database="test",
                    user="test",
                    password="test",
                    host="localhost",
                    port=forward_port,
                )
                conn.close()
                break
            except:
                time.sleep(1)
                continue

        yield forward_port

    finally:
        if p is not None:
            print("Terminating port-forwarding")
            p.terminate()


@pytest.fixture(scope="session")
def helm_postgres_url_for_k8s_run_launcher(helm_namespace_for_k8s_run_launcher):
    with local_port_forward_postgres(
        namespace=helm_namespace_for_k8s_run_launcher
    ) as local_forward_port:
        postgres_url = "postgresql://test:test@localhost:{local_forward_port}/test".format(
            local_forward_port=local_forward_port
        )
        print("Local Postgres forwarding URL: ", postgres_url)
        yield postgres_url


@pytest.fixture(scope="session")
def helm_postgres_url_for_user_deployments_subchart_disabled(
    helm_namespace_for_user_deployments_subchart_disabled,
):  # pylint: disable=unused-argument, redefined-outer-name
    with local_port_forward_postgres(
        namespace=helm_namespace_for_user_deployments_subchart_disabled
    ) as local_forward_port:
        postgres_url = "postgresql://test:test@localhost:{local_forward_port}/test".format(
            local_forward_port=local_forward_port
        )
        print("Local Postgres forwarding URL: ", postgres_url)
        yield postgres_url


@pytest.fixture(scope="function")
def dagster_instance_for_user_deployments_subchart_disabled(
    helm_postgres_url_for_user_deployments_subchart_disabled,
):  # pylint: disable=redefined-outer-name
    tempdir = DagsterInstance.temp_storage()

    with DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=PostgresRunStorage(helm_postgres_url_for_user_deployments_subchart_disabled),
        event_storage=PostgresEventLogStorage(
            helm_postgres_url_for_user_deployments_subchart_disabled
        ),
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=DefaultRunCoordinator(),
        run_launcher=ExplodingRunLauncher(),
    ) as instance:
        yield instance

        check_export_runs(instance)


@pytest.fixture(scope="session")
def helm_postgres_url_for_daemon(helm_namespace_for_daemon):
    with local_port_forward_postgres(namespace=helm_namespace_for_daemon) as local_forward_port:
        postgres_url = "postgresql://test:test@localhost:{local_forward_port}/test".format(
            local_forward_port=local_forward_port
        )
        print("Local Postgres forwarding URL: ", postgres_url)
        yield postgres_url


@pytest.fixture(scope="function")
def dagster_instance_for_daemon(
    helm_postgres_url_for_daemon,
):  # pylint: disable=redefined-outer-name
    tempdir = DagsterInstance.temp_storage()

    with DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=PostgresRunStorage(helm_postgres_url_for_daemon),
        event_storage=PostgresEventLogStorage(helm_postgres_url_for_daemon),
        schedule_storage=PostgresScheduleStorage(helm_postgres_url_for_daemon),
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=QueuedRunCoordinator(),
        run_launcher=ExplodingRunLauncher(),
        scheduler=DagsterDaemonScheduler(),
    ) as instance:
        yield instance

        check_export_runs(instance)


@pytest.fixture(scope="function")
def dagster_instance_for_k8s_run_launcher(
    helm_postgres_url_for_k8s_run_launcher,
):  # pylint: disable=redefined-outer-name
    tempdir = DagsterInstance.temp_storage()

    instance_ref = InstanceRef.from_dir(tempdir)

    with DagsterInstance(
        instance_type=InstanceType.PERSISTENT,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=PostgresRunStorage(helm_postgres_url_for_k8s_run_launcher),
        event_storage=PostgresEventLogStorage(helm_postgres_url_for_k8s_run_launcher),
        schedule_storage=PostgresScheduleStorage(helm_postgres_url_for_k8s_run_launcher),
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=DefaultRunCoordinator(),
        run_launcher=ExplodingRunLauncher(),
        ref=instance_ref,
    ) as instance:
        yield instance

        check_export_runs(instance)


@pytest.fixture(scope="session")
def helm_postgres_url(helm_namespace):
    with local_port_forward_postgres(namespace=helm_namespace) as local_forward_port:
        postgres_url = "postgresql://test:test@localhost:{local_forward_port}/test".format(
            local_forward_port=local_forward_port
        )
        print("Local Postgres forwarding URL: ", postgres_url)
        yield postgres_url


@pytest.fixture(scope="function")
def dagster_instance(helm_postgres_url):  # pylint: disable=redefined-outer-name

    with tempfile.TemporaryDirectory() as tempdir:
        with environ({"DAGSTER_HOME": tempdir}):

            with DagsterInstance(
                instance_type=InstanceType.PERSISTENT,
                local_artifact_storage=LocalArtifactStorage(tempdir),
                run_storage=PostgresRunStorage(helm_postgres_url),
                event_storage=PostgresEventLogStorage(helm_postgres_url),
                compute_log_manager=NoOpComputeLogManager(),
                run_coordinator=DefaultRunCoordinator(),
                run_launcher=ExplodingRunLauncher(),  # use graphql to launch any runs
                ref=InstanceRef.from_dir(tempdir),
            ) as instance:
                yield instance

                check_export_runs(instance)


def check_export_runs(instance):
    if not IS_BUILDKITE:
        return

    # example PYTEST_CURRENT_TEST: test_user_code_deployments.py::test_execute_on_celery_k8s (teardown)
    current_test = (
        os.environ.get("PYTEST_CURRENT_TEST").split()[0].replace("::", "-").replace(".", "-")
    )

    for run in instance.get_runs():
        output_file = f"{current_test}-{run.run_id}.dump"

        try:
            export_run(instance, run, output_file)
        except Exception as e:
            print(f"Hit an error exporting dagster-debug {output_file}: {e}")
            continue

        p = subprocess.Popen(
            [
                "buildkite-agent",
                "artifact",
                "upload",
                output_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        print("Buildkite artifact added with stdout: ", stdout)
        print("Buildkite artifact added with stderr: ", stderr)
        assert p.returncode == 0
