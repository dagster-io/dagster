import os
import subprocess
import sys
import uuid

import pytest
import six
from dagster_k8s.launcher import K8sRunLauncher
from kubernetes import client, config

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


def git_repository_root():
    return six.ensure_str(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip())


def test_repo_path():
    return os.path.join(git_repository_root(), '.buildkite', 'images', 'docker', 'test_project')


def environments_path():
    return os.path.join(test_repo_path(), 'test_pipelines', 'environments')


@pytest.fixture(scope='session')
def kubeconfig_file():
    with safe_tempfile_path() as path:
        yield path


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
def docker_image(docker_full_image_name, docker_image_tag, cluster_exists):

    if not IS_BUILDKITE and not cluster_exists:
        # We build the image because we aren't guaranteed to have it
        base_image = 'dagster/buildkite-integration:{docker_image_tag}'.format(
            docker_image_tag=docker_image_tag
        )
        build_script = os.path.join(test_repo_path(), 'build.sh')
        subprocess.check_call([build_script, base_image])
        subprocess.check_call(['docker', 'tag', DOCKER_IMAGE_NAME, docker_full_image_name])

    return docker_full_image_name


@pytest.fixture(scope='session')
def cluster_exists(cluster_name):
    running_clusters = (
        subprocess.check_output(['kind', 'get', 'clusters']).decode('utf-8').split('\n')
    )

    return cluster_name in running_clusters


@pytest.fixture(scope='session')
def setup_cluster(cluster_name, cluster_exists):  # pylint: disable=redefined-outer-name

    if not IS_BUILDKITE and cluster_exists:
        yield cluster_name
        return
    else:
        try:
            print(
                '--- \033[32m:k8s: Running kind cluster setup for cluster '
                '{cluster_name}\033[0m'.format(cluster_name=cluster_name)
            )
            subprocess.check_call(['kind', 'create', 'cluster', '--name', cluster_name])
            yield cluster_name
        finally:
            # ensure cleanup happens on error or normal exit
            subprocess.check_call('kind delete cluster --name %s' % cluster_name, shell=True)


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
        subprocess.check_call(
            'aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True
        )

    # see https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
    print('Syncing to nodes...')
    config.load_kube_config(config_file=kubeconfig)

    if not IS_BUILDKITE:
        subprocess.check_call(
            ['kind', 'load', 'docker-image', '--name', setup_cluster, docker_image]
        )
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
        subprocess.check_call(cmd, shell=True)

        # restart kubelet to pick up the config
        print('Restarting node kubelets...')
        subprocess.check_call(
            'docker exec %s systemctl restart kubelet.service' % node_name, shell=True
        )

    yield cluster


@pytest.fixture(scope='session')
def helm_chart(
    cluster, docker_image, image_pull_policy,
):  # pylint: disable=redefined-outer-name,unused-argument
    print('--- \033[32m:helm: Installing Helm chart\033[0m"')

    # Install helm chart
    try:
        subprocess.check_call(
            '''helm install \
        --set dagit.image="{docker_image}" \\
        --set job_image="{docker_image}" \\
        --set imagePullPolicy="{image_pull_policy}" \\
        --set serviceAccount.name="dagit-admin" \\
        dagster \\
        helm/dagster/'''.format(
                docker_image=docker_image, image_pull_policy=image_pull_policy,
            ),
            shell=True,
            cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
        )
        success, _ = wait_for_pod('dagit')
        assert success
        yield
    finally:
        subprocess.check_call(
            ['helm uninstall dagster'],
            shell=True,
            cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
        )


@pytest.fixture(scope='session')
def run_launcher(
    helm_chart, docker_image, kubeconfig_file, image_pull_policy
):  # pylint: disable=redefined-outer-name,unused-argument
    return K8sRunLauncher(
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        job_image=docker_image,
        load_kubeconfig=True,
        kubeconfig_file=kubeconfig_file,
        image_pull_policy=image_pull_policy,
    )
