import os
import subprocess
import time
from contextlib import contextmanager

import psycopg2
import pytest
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.utils import wait_for_pod
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage

from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.instance.ref import compute_logs_directory
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage

from .cluster import define_cluster_provider_fixture
from .helm import helm_chart, helm_test_resources, test_namespace
from .utils import IS_BUILDKITE, check_output, find_free_port

# How long to wait before giving up on trying to establish postgres port forwarding
PG_PORT_FORWARDING_TIMEOUT = 60  # 1 minute


@pytest.fixture(scope='session', autouse=True)
def dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    os.environ['DAGSTER_HOME'] = '/opt/dagster/dagster_home'
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


@pytest.fixture(scope='session')
def image_pull_policy():
    # This is because when running local tests, we need to load the image into the kind cluster (and
    # then not attempt to pull it) because we don't want to require credentials for a private
    # registry / pollute the private registry / set up and network a local registry as a condition
    # of running tests
    if IS_BUILDKITE:
        return 'Always'
    else:
        return 'IfNotPresent'


cluster_provider = define_cluster_provider_fixture(
    additional_kind_images=['docker.io/bitnami/rabbitmq', 'docker.io/bitnami/postgresql']
)


@pytest.fixture(scope='session')
def helm_namespace(
    image_pull_policy, cluster_provider, request
):  # pylint: disable=unused-argument, redefined-outer-name
    '''If an existing Helm chart namespace is specified via pytest CLI with the argument
    --existing-helm-namespace, we will use that chart.

    Otherwise, provision a test namespace and install Helm chart into that namespace.

    Yields the Helm chart namespace.
    '''
    from .test_project import test_project_docker_image

    existing_helm_namespace = request.config.getoption('--existing-helm-namespace')

    if existing_helm_namespace:
        yield existing_helm_namespace

    else:
        # Never bother cleaning up on Buildkite
        if IS_BUILDKITE:
            should_cleanup = False
        # Otherwise, always clean up unless --no-cleanup specified
        else:
            should_cleanup = not request.config.getoption('--no-cleanup')

        with test_namespace(should_cleanup) as namespace:
            with helm_test_resources(namespace, should_cleanup):
                docker_image = test_project_docker_image()
                with helm_chart(namespace, image_pull_policy, docker_image, should_cleanup):
                    print('Helm chart successfully installed in namespace %s' % namespace)
                    yield namespace


@pytest.fixture(scope='session')
def run_launcher(
    cluster_provider, image_pull_policy, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument
    from .test_project import test_project_docker_image

    return K8sRunLauncher(
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        postgres_password_secret='dagster-postgresql-secret',
        dagster_home='/opt/dagster/dagster_home',
        job_image=test_project_docker_image(),
        load_kubeconfig=True,
        kubeconfig_file=cluster_provider.kubeconfig_file,
        image_pull_policy=image_pull_policy,
        job_namespace=helm_namespace,
        env_config_maps=['dagster-job-runner-env', 'test-env-configmap'],
        env_secrets=['test-env-secret'],
    )


@pytest.fixture(scope='session')
def dagster_instance(helm_namespace, run_launcher):  # pylint: disable=redefined-outer-name
    @contextmanager
    def local_port_forward_postgres():
        print('Port-forwarding postgres')
        postgres_pod_name = (
            check_output(
                [
                    'kubectl',
                    'get',
                    'pods',
                    '--namespace',
                    helm_namespace,
                    '-l',
                    'app=postgresql,release=dagster',
                    '-o',
                    'jsonpath="{.items[0].metadata.name}"',
                ]
            )
            .decode('utf-8')
            .strip('"')
        )
        forward_port = find_free_port()

        wait_for_pod(postgres_pod_name, namespace=helm_namespace)

        try:
            p = subprocess.Popen(
                [
                    'kubectl',
                    'port-forward',
                    '--namespace',
                    helm_namespace,
                    postgres_pod_name,
                    '{forward_port}:5432'.format(forward_port=forward_port),
                ]
            )

            # Validate port forwarding works
            start = time.time()

            while True:
                if time.time() - start > PG_PORT_FORWARDING_TIMEOUT:
                    raise Exception('Timed out while waiting for postgres port forwarding')

                print(
                    'Waiting for port forwarding from k8s pod %s:5432 to localhost:%d to be'
                    ' available...' % (postgres_pod_name, forward_port)
                )
                try:
                    conn = psycopg2.connect(
                        database='test',
                        user='test',
                        password='test',
                        host='localhost',
                        port=forward_port,
                    )
                    conn.close()
                    break
                except:  # pylint: disable=bare-except, broad-except
                    pass
                time.sleep(1)

            yield forward_port

        finally:
            print('Terminating port-forwarding')
            p.terminate()

    tempdir = DagsterInstance.temp_storage()

    with local_port_forward_postgres() as local_forward_port:
        postgres_url = 'postgresql://test:test@localhost:{local_forward_port}/test'.format(
            local_forward_port=local_forward_port
        )
        print('Local Postgres forwarding URL: ', postgres_url)

        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(tempdir),
            run_storage=PostgresRunStorage(postgres_url),
            event_storage=PostgresEventLogStorage(postgres_url),
            compute_log_manager=NoOpComputeLogManager(compute_logs_directory(tempdir)),
            run_launcher=run_launcher,
        )
        yield instance
