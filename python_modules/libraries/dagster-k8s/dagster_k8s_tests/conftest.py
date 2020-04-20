import os
import subprocess
import sys
import time
from contextlib import contextmanager

import kubernetes
import psycopg2
import pytest
from dagster_k8s.launcher import K8sRunLauncher
from dagster_k8s.utils import wait_for_pod
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage

from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.instance.ref import compute_logs_directory
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage

from .cluster_config import ClusterConfig
from .helm import helm_chart, helm_test_resources, test_namespace
from .kind_cluster import kind_cluster, kind_cluster_exists
from .utils import check_output, find_free_port, test_repo_path

IS_BUILDKITE = os.getenv('BUILDKITE') is not None

# This is the name of the image built by build.sh / present on buildkite which we use for all of
# our tests
DOCKER_IMAGE_NAME = 'dagster-docker-buildkite'

# This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
# `docker.io/` and attempting to pull images from Docker Hub
LOCAL_DOCKER_REPOSITORY = 'dagster.io.priv'


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


# pylint:disable=redefined-outer-name
@pytest.fixture(scope='session')
def docker_image():
    docker_repository = os.getenv('DAGSTER_DOCKER_REPOSITORY')
    image_name = os.getenv('DAGSTER_DOCKER_IMAGE', DOCKER_IMAGE_NAME)
    docker_image_tag = os.getenv('DAGSTER_DOCKER_IMAGE_TAG')

    if IS_BUILDKITE:
        assert docker_image_tag is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set '
            'to proceed'
        )
        assert docker_repository is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set '
            'to proceed'
        )

    if not docker_repository:
        docker_repository = LOCAL_DOCKER_REPOSITORY

    if not docker_image_tag:
        # Detect the python version we're running on
        majmin = str(sys.version_info.major) + str(sys.version_info.minor)

        docker_image_tag = 'py{majmin}-{image_version}'.format(
            majmin=majmin, image_version='latest'
        )

    final_docker_image = '{repository}/{image_name}:{tag}'.format(
        repository=docker_repository, image_name=image_name, tag=docker_image_tag
    )
    print('Using Docker image: %s' % final_docker_image)
    return final_docker_image


def kind_build_and_load_images(local_dagster_image, cluster_name):
    print('Building and loading images into kind cluster...')

    # We build the image because we aren't guaranteed to have it
    base_python = '.'.join(
        [str(x) for x in [sys.version_info.major, sys.version_info.minor, sys.version_info.micro]]
    )

    # Build and tag local dagster test image
    build_script = os.path.join(test_repo_path(), 'build.sh')
    check_output([build_script, base_python])
    check_output(['docker', 'tag', DOCKER_IMAGE_NAME, local_dagster_image])

    # Pull rabbitmq/pg images
    check_output(['docker', 'pull', 'docker.io/bitnami/rabbitmq'])
    check_output(['docker', 'pull', 'docker.io/bitnami/postgresql'])

    # load all images into the kind cluster
    for image in [
        'docker.io/bitnami/postgresql',
        'docker.io/bitnami/rabbitmq',
        local_dagster_image,
    ]:
        check_output(['kind', 'load', 'docker-image', '--name', cluster_name, image])


@pytest.fixture(scope='session')
def cluster_provider(request, docker_image):
    if IS_BUILDKITE:
        print('Installing ECR credentials...')
        check_output('aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True)

    cluster_provider = request.config.getoption('--cluster-provider')

    # Use a kind cluster
    if cluster_provider == 'kind':
        cluster_name = request.config.getoption('--kind-cluster')

        # Cluster will be deleted afterwards unless this is set.
        # This is to allow users to reuse an existing cluster in local test by running
        # `pytest --kind-cluster my-cluster --no-cleanup` -- this avoids the per-test run overhead
        # of cluster setup and teardown
        should_cleanup = not request.config.getoption('--no-cleanup')

        existing_cluster = kind_cluster_exists(cluster_name)

        with kind_cluster(cluster_name, should_cleanup=should_cleanup) as cluster_config:
            if not IS_BUILDKITE and not existing_cluster:
                kind_build_and_load_images(docker_image, cluster_config.name)
            yield cluster_config

    # Use cluster from kubeconfig
    elif cluster_provider == 'kubeconfig':
        kubeconfig_file = os.getenv('KUBECONFIG', os.path.expandvars('${HOME}/.kube/config'))
        kubernetes.config.load_kube_config(config_file=kubeconfig_file)
        yield ClusterConfig(name='from_system_kubeconfig', kubeconfig_file=kubeconfig_file)

    else:
        raise Exception('unknown cluster provider %s' % cluster_provider)


@pytest.fixture(scope='session')
def helm_namespace(
    image_pull_policy, docker_image, cluster_provider, request
):  # pylint: disable=unused-argument
    '''If an existing Helm chart namespace is specified via pytest CLI with the argument
    --existing-helm-namespace, we will use that chart.

    Otherwise, provision a test namespace and install Helm chart into that namespace.

    Yields the Helm chart namespace.
    '''
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
                with helm_chart(namespace, image_pull_policy, docker_image, should_cleanup):
                    print('Helm chart successfully installed in namespace %s' % namespace)
                    yield namespace


@pytest.fixture(scope='session')
def run_launcher(
    docker_image, cluster_provider, image_pull_policy, helm_namespace
):  # pylint: disable=redefined-outer-name,unused-argument

    return K8sRunLauncher(
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        postgres_password_secret='dagster-postgresql-secret',
        dagster_home='/opt/dagster/dagster_home',
        job_image=docker_image,
        load_kubeconfig=True,
        kubeconfig_file=cluster_provider.kubeconfig_file,
        image_pull_policy=image_pull_policy,
        job_namespace=helm_namespace,
        env_config_maps=['dagster-job-runner-env', 'test-env-configmap'],
        env_secrets=['test-env-secret'],
    )


@pytest.fixture(scope='session')
def dagster_instance(helm_namespace, run_launcher):
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
