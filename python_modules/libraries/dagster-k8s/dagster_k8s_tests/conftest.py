import base64
import os
import subprocess
import sys
import time
from collections import namedtuple

import pytest
import six
import yaml
from dagster_k8s.launcher import K8sRunLauncher
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage
from kubernetes import client, config

from dagster import check
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.instance.ref import compute_logs_directory
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage

from .kind_cluster import kind_cluster
from .utils import check_output, find_free_port, git_repository_root, test_repo_path, wait_for_pod

IS_BUILDKITE = os.getenv('BUILDKITE') is not None

# This is the name of the image built by build.sh / present on buildkite which we use for all of
# our tests
DOCKER_IMAGE_NAME = 'dagster-docker-buildkite'

# This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
# `docker.io/` and attempting to pull images from Docker Hub
LOCAL_DOCKER_REPOSITORY = 'dagster.io.priv'

# Detect the python version we're running on
MAJMIN = str(sys.version_info.major) + str(sys.version_info.minor)


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
        docker_image_tag = 'py{majmin}-{image_version}'.format(
            majmin=MAJMIN, image_version='latest'
        )

    final_docker_image = '{repository}/{image_name}:{tag}'.format(
        repository=docker_repository, image_name=image_name, tag=docker_image_tag
    )
    print('Using Docker image: %s' % final_docker_image)
    return final_docker_image


def kind_build_and_load_images(local_dagster_image, cluster_name):
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


class ClusterConfig(namedtuple('_ClusterConfig', 'name kubeconfig_file')):
    '''Used to represent a cluster, returned by the cluster_provider fixture below.
    '''

    def __new__(cls, name, kubeconfig_file):
        return super(ClusterConfig, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            kubeconfig_file=check.str_param(kubeconfig_file, 'kubeconfig_file'),
        )


@pytest.fixture(scope='session')
def cluster_provider(request, docker_image):
    if IS_BUILDKITE:
        print('Installing ECR credentials...')
        check_output('aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True)

    cluster_provider = request.config.getoption('--cluster-provider')

    # Use a kind cluster
    if cluster_provider == 'kind':
        cluster_name = request.config.getoption("--kind-cluster")

        # Cluster will be deleted afterwards unless this is set.
        # This is to allow users to reuse an existing cluster in local test by running
        # `pytest --kind-cluster my-cluster` -- this avoids the per-test run overhead of cluster
        # setup and teardown
        keep_cluster = request.config.getoption("--keep-cluster")

        with kind_cluster(cluster_name, keep_cluster) as (cluster_name, kubeconfig_file):
            if not IS_BUILDKITE:
                kind_build_and_load_images(docker_image, cluster_name)

            yield ClusterConfig(cluster_name, kubeconfig_file)

    # Use cluster from kubeconfig
    elif cluster_provider == 'kubeconfig':
        kubeconfig_file = os.getenv('KUBECONFIG', os.path.expandvars('${HOME}/.kube/config'))
        config.load_kube_config(config_file=kubeconfig_file)
        yield ClusterConfig(name='from_system_kubeconfig', kubeconfig_file=kubeconfig_file)

    else:
        raise Exception('unknown cluster provider %s' % cluster_provider)


@pytest.fixture(scope='session')
def helm_chart(
    cluster_provider, docker_image, image_pull_policy
):  # pylint: disable=redefined-outer-name,unused-argument
    print('--- \033[32m:helm: Installing Helm chart\033[0m')

    # Install helm chart
    try:
        check_output('''kubectl create namespace dagster-test''', shell=True)

        print('Creating k8s test objects ConfigMap test-env-configmap and Secret test-env-secret')
        kube_api = client.CoreV1Api()

        configmap = client.V1ConfigMap(
            api_version='v1',
            kind='ConfigMap',
            data={'TEST_ENV_VAR': 'foobar'},
            metadata=client.V1ObjectMeta(name='test-env-configmap'),
        )
        kube_api.create_namespaced_config_map(namespace='dagster-test', body=configmap)

        # Secret values are expected to be base64 encoded
        secret_val = six.ensure_str(base64.b64encode(six.ensure_binary('foobar')))
        secret = client.V1Secret(
            api_version='v1',
            kind='Secret',
            data={'TEST_SECRET_ENV_VAR': secret_val},
            metadata=client.V1ObjectMeta(name='test-env-secret'),
        )
        kube_api.create_namespaced_secret(namespace='dagster-test', body=secret)

        try:
            repository, tag = docker_image.split(':')

            helm_config = {
                'imagePullPolicy': image_pull_policy,
                'dagit': {
                    'image': {'repository': repository, 'tag': tag},
                    'env': {'TEST_SET_ENV_VAR': 'test_dagit_env_var'},
                    'env_config_maps': ['test-env-configmap'],
                    'env_secrets': ['test-env-secret'],
                },
                'job_runner': {
                    'image': {'repository': repository, 'tag': tag},
                    'env': {'TEST_SET_ENV_VAR': 'test_job_runner_env_var'},
                    'env_config_maps': ['test-env-configmap'],
                    'env_secrets': ['test-env-secret'],
                },
                'serviceAccount': {'name': 'dagit-admin'},
                'postgresqlPassword': 'test',
                'postgresqlDatabase': 'test',
                'postgresqlUser': 'test',
                'celery': {
                    'extraWorkerQueues': [
                        {'name': 'extra-queue-1', 'replicaCount': 1},
                        {'name': 'extra-queue-2', 'replicaCount': 2},
                    ]
                },
            }
            helm_config_yaml = yaml.dump(helm_config, default_flow_style=False)

            helm_cmd = [
                'helm',
                'install',
                '--namespace',
                'dagster-test',
                '-f',
                '-',
                'dagster',
                'helm/dagster/',
            ]

            print('Running Helm Install: \n', helm_cmd, '\nwith config:\n', helm_config_yaml)

            p = subprocess.Popen(
                helm_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            stdout, stderr = p.communicate(six.ensure_binary(helm_config_yaml))
            print('\n\nstdout:\n', six.ensure_str(stdout))
            print('\n\nstderr:\n', six.ensure_str(stderr))
            assert p.returncode == 0

            check_output(
                helm_cmd,
                shell=True,
                cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
            )

            # Wait for Dagit pod to be ready (won't actually stay up w/out js rebuild)
            success, _ = wait_for_pod('dagit')
            assert success

            # Wait for additional Celery worker queues to become ready
            pods = kube_api.list_namespaced_pod(namespace='dagster-test')
            for extra_queue in helm_config['celery']['extraWorkerQueues']:
                pod_names = [
                    p.metadata.name for p in pods.items if extra_queue['name'] in p.metadata.name
                ]
                assert len(pod_names) == extra_queue['replicaCount']
                for pod in pod_names:
                    success, _ = wait_for_pod(pod)
                    assert success

            yield

        finally:
            print('Uninstalling helm chart')
            check_output(
                ['helm uninstall dagster --namespace dagster-test'],
                shell=True,
                cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
            )
    finally:
        if not IS_BUILDKITE:
            print('Deleting namespace')
            check_output(
                ['kubectl delete namespace dagster-test'], shell=True,
            )
            print('Deleted namespace')


@pytest.fixture(scope='session')
def run_launcher(
    helm_chart, docker_image, cluster_provider, image_pull_policy
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
        job_namespace='dagster-test',
        env_config_maps=['dagster-job-runner-env', 'test-env-configmap'],
        env_secrets=['test-env-secret'],
    )


@pytest.fixture(scope='session')
def network_postgres(helm_chart):  # pylint:disable=unused-argument
    print('Port-forwarding postgres')
    postgres_pod_name = (
        check_output(
            [
                'kubectl',
                'get',
                'pods',
                '--namespace',
                'dagster-test',
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
    success, _ = wait_for_pod(postgres_pod_name, wait_for_readiness=True)
    assert success
    try:
        p = subprocess.Popen(
            [
                'kubectl',
                'port-forward',
                '--namespace',
                'dagster-test',
                postgres_pod_name,
                '{forward_port}:5432'.format(forward_port=forward_port),
            ]
        )
        time.sleep(1)
        yield forward_port

    finally:
        print('Terminating port-forwarding')
        p.terminate()


@pytest.fixture(scope='session')
def dagster_instance(run_launcher, network_postgres):

    tempdir = DagsterInstance.temp_storage()

    postgres_url = 'postgresql://test:test@localhost:{network_postgres}/test'.format(
        network_postgres=network_postgres
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
    return instance
