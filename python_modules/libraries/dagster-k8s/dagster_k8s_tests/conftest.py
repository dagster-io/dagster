import base64
import os
import socket
import subprocess
import sys
import time
import uuid
from contextlib import closing

import pytest
import six
import yaml
from dagster_k8s.launcher import K8sRunLauncher
from dagster_postgres import PostgresEventLogStorage, PostgresRunStorage
from kubernetes import client, config

from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.instance.ref import compute_logs_directory
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.utils import safe_tempfile_path

from .utils import wait_for_pod

TOX_PYTHON_VERSION = 'py37'

IS_BUILDKITE = os.getenv('BUILDKITE') is not None

# This is the name of the image built by build.sh / present on buildkite which we use for all of
# our tests
DOCKER_IMAGE_NAME = 'dagster-docker-buildkite'

# This needs to be a domain name to avoid the k8s machinery automatically prefixing it with
# `docker.io/` and attempting to pull images from Docker Hub
LOCAL_DOCKER_REPOSITORY = 'dagster.io'

# Detect the python version we're running on
MAJMIN = str(sys.version_info.major) + str(sys.version_info.minor)


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        six.raise_from(Exception(output), exc)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def git_repository_root():
    return six.ensure_str(check_output(['git', 'rev-parse', '--show-toplevel']).strip())


def test_repo_path():
    return os.path.join(git_repository_root(), '.buildkite', 'images', 'docker', 'test_project')


def environments_path():
    return os.path.join(test_repo_path(), 'test_pipelines', 'environments')


@pytest.fixture(scope='session', autouse=True)
def dagster_home():
    old_env = os.getenv('DAGSTER_HOME')
    os.environ['DAGSTER_HOME'] = '/opt/dagster/dagster_home'
    yield
    if old_env is not None:
        os.environ['DAGSTER_HOME'] = old_env


@pytest.fixture(scope='session')
def kubeconfig_file():
    with safe_tempfile_path() as path:
        yield path


@pytest.fixture(scope='session')
def base_python():
    return '.'.join(
        [str(x) for x in [sys.version_info.major, sys.version_info.minor, sys.version_info.micro]]
    )


@pytest.fixture(scope='session')
def cluster_name(request):
    # This is to allow users to reuse an existing cluster in local test by running
    # `pytest --cluster my-cluster` -- this avoids the per-test run overhead of cluster setup
    # and teardown
    return request.config.getoption("--cluster") or 'kind-cluster-{uuid}'.format(
        uuid=uuid.uuid4().hex
    )


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


@pytest.fixture(scope='session')
def docker_repository():
    docker_repository_env = os.getenv('DAGSTER_DOCKER_REPOSITORY')
    if IS_BUILDKITE:
        assert docker_repository_env is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set '
            'to proceed'
        )
        return docker_repository_env
    else:
        assert docker_repository_env is None, (
            'When executing locally, this test requires the environment variable '
            'DAGSTER_DOCKER_REPOSITORY to be unset to proceed'
        )
        return LOCAL_DOCKER_REPOSITORY


@pytest.fixture(scope='session')
def docker_image_tag():
    docker_image_tag_env = os.getenv('DAGSTER_DOCKER_IMAGE_TAG')

    if IS_BUILDKITE:
        assert docker_image_tag_env is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set '
            'to proceed'
        )
        return docker_image_tag_env
    else:
        return 'py{majmin}-{image_version}'.format(majmin=MAJMIN, image_version='latest')


# pylint:disable=redefined-outer-name
@pytest.fixture(scope='session')
def docker_full_image_name(docker_repository, docker_image_tag):
    return '{repository}/{image}:{tag}'.format(
        repository=docker_repository, image=DOCKER_IMAGE_NAME, tag=docker_image_tag
    )


@pytest.fixture(scope='session')
def docker_image(docker_full_image_name, base_python, cluster_exists):

    if not IS_BUILDKITE and not cluster_exists:
        # We build the image because we aren't guaranteed to have it
        build_script = os.path.join(test_repo_path(), 'build.sh')
        check_output([build_script, base_python])
        check_output(['docker', 'tag', DOCKER_IMAGE_NAME, docker_full_image_name])

    return docker_full_image_name


@pytest.fixture(scope='session')
def cluster_exists(cluster_name):
    running_clusters = check_output(['kind', 'get', 'clusters']).decode('utf-8').split('\n')

    return cluster_name in running_clusters


@pytest.fixture(scope='session')
def setup_cluster(request, cluster_name, cluster_exists):  # pylint: disable=redefined-outer-name

    if not IS_BUILDKITE and cluster_exists:
        yield cluster_name
        return
    else:
        try:
            print(
                '--- \033[32m:k8s: Running kind cluster setup for cluster '
                '{cluster_name}\033[0m'.format(cluster_name=cluster_name)
            )
            check_output(['kind', 'create', 'cluster', '--name', cluster_name])
            yield cluster_name
        finally:
            if not request.config.getoption("--keep-cluster"):
                # ensure cleanup happens on error or normal exit
                print('Cleaning up kind cluster {cluster_name}'.format(cluster_name=cluster_name))
                check_output('kind delete cluster --name %s' % cluster_name, shell=True)


@pytest.fixture(scope='session')
def kubeconfig(setup_cluster, kubeconfig_file):  # pylint: disable=redefined-outer-name
    cluster_name = setup_cluster
    old_kubeconfig = os.getenv('KUBECONFIG')
    try:
        print('Writing kubeconfig to file %s' % kubeconfig_file)
        if not IS_BUILDKITE and sys.platform == 'darwin':
            kubeconfig_call = 'kind get kubeconfig --name {cluster_name}'.format(
                cluster_name=cluster_name
            )
        else:
            kubeconfig_call = 'kind get kubeconfig --internal --name {cluster_name}'.format(
                cluster_name=cluster_name
            )

        with open(kubeconfig_file, 'wb') as f:
            subprocess.check_call(
                kubeconfig_call, stdout=f, shell=True,
            )
        os.environ['KUBECONFIG'] = kubeconfig_file

        yield kubeconfig_file

    finally:
        print('Cleaning up kubeconfig')
        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        if old_kubeconfig is not None:
            os.environ['KUBECONFIG'] = old_kubeconfig


@pytest.fixture(scope='session')
def cluster(
    setup_cluster, kubeconfig, docker_image,
):  # pylint: disable=redefined-outer-name
    # Need a unique cluster name for this job; can't have hyphens
    if IS_BUILDKITE:
        print('Installing ECR credentials...')
        check_output('aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True)

    # see https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
    print('Syncing kubeconfig to nodes...')
    config.load_kube_config(config_file=kubeconfig)

    if not IS_BUILDKITE:
        check_output(['kind', 'load', 'docker-image', '--name', setup_cluster, docker_image])

        # rabbitmq
        check_output(['docker', 'pull', 'docker.io/bitnami/rabbitmq'])
        check_output(
            ['kind', 'load', 'docker-image', '--name', setup_cluster, 'bitnami/rabbitmq:latest']
        )

        # postgres
        check_output(['docker', 'pull', 'docker.io/bitnami/postgresql'])
        check_output(
            ['kind', 'load', 'docker-image', '--name', setup_cluster, 'bitnami/postgresql:latest']
        )

    # https://github.com/kubernetes-client/python/issues/895#issuecomment-515025300
    from kubernetes.client.models.v1_container_image import V1ContainerImage

    def names(self, names):
        self._names = names  # pylint: disable=protected-access

    V1ContainerImage.names = V1ContainerImage.names.setter(names)  # pylint: disable=no-member

    nodes = client.CoreV1Api().list_node().items
    for node in nodes:
        node_name = node.metadata.name

        if IS_BUILDKITE:
            docker_exe = '/usr/bin/docker'
        else:
            docker_exe = 'docker'
        # copy the config to where kubelet will look
        cmd = os.path.expandvars(
            '{docker_exe} cp $HOME/.docker/config.json '
            '{node_name}:/var/lib/kubelet/config.json'.format(
                docker_exe=docker_exe, node_name=node_name
            )
        )
        check_output(cmd, shell=True)

        # restart kubelet to pick up the config
        print('Restarting node kubelets...')
        check_output('docker exec %s systemctl restart kubelet.service' % node_name, shell=True)

    yield cluster


@pytest.fixture(scope='session')
def helm_chart(
    kubeconfig, cluster, docker_image, image_pull_policy
):  # pylint: disable=redefined-outer-name,unused-argument
    print('--- \033[32m:helm: Installing Helm chart\033[0m')

    # Install helm chart
    try:
        check_output('''kubectl create namespace dagster-test''', shell=True)

        print('Creating k8s test objects ConfigMap test-env-configmap and Secret test-env-secret')
        config.load_kube_config(config_file=kubeconfig)
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
    helm_chart, docker_image, kubeconfig_file, image_pull_policy
):  # pylint: disable=redefined-outer-name,unused-argument
    return K8sRunLauncher(
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        dagster_home='/opt/dagster/dagster_home',
        job_image=docker_image,
        load_kubeconfig=True,
        kubeconfig_file=kubeconfig_file,
        image_pull_policy=image_pull_policy,
        job_namespace='dagster-test',
        env_config_maps=['test-env-configmap'],
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
    instance = DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(tempdir),
        run_storage=PostgresRunStorage(postgres_url),
        event_storage=PostgresEventLogStorage(postgres_url),
        compute_log_manager=NoOpComputeLogManager(compute_logs_directory(tempdir)),
        run_launcher=run_launcher,
    )
    return instance
