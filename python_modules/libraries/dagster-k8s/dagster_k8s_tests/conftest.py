import os
import subprocess
import sys
import uuid

import pytest
import six
from dagster_k8s.launcher import K8sRunLauncher
from kubernetes import client, config

from .utils import wait_for_pod

TOX_PYTHON_VERSION = 'py37'

KUBECONFIG_FILE = '/tmp/kubeconfig'

IS_BUILDKITE = os.getenv('BUILDKITE') is not None

DOCKER_IMAGE_NAME = 'dagster-docker-buildkite'


def git_repository_root():
    return six.ensure_str(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip())


def test_repo_path():
    return os.path.join(git_repository_root(), '.buildkite', 'images', 'docker', 'test_project')


def environments_path():
    return os.path.join(test_repo_path(), 'test_pipelines', 'environments')


@pytest.fixture(scope='session')
def cluster_name():
    return 'kindcluster{uuid}'.format(uuid=uuid.uuid4().hex)


@pytest.fixture(scope='session')
def docker_repository():
    docker_repository_ = os.getenv('DAGSTER_DOCKER_REPOSITORY')
    if IS_BUILDKITE:
        assert docker_repository_ is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set '
            'to proceed'
        )
        return docker_repository_

    assert docker_repository_ is None, (
        'When executing locally, this test requires the environment variable '
        'DAGSTER_DOCKER_REPOSITORY to be unset to proceed'
    )
    return 'dagster'


@pytest.fixture(scope='session')
def docker_image_tag():
    docker_image_tag_ = os.getenv('DAGSTER_DOCKER_IMAGE_TAG')

    if IS_BUILDKITE:
        assert docker_image_tag_ is not None, (
            'This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set '
            'to proceed'
        )

    if docker_image_tag_ is not None:
        return docker_image_tag_

    majmin = str(sys.version_info.major) + str(sys.version_info.minor)
    return 'py{majmin}-{image_version}'.format(majmin=majmin, image_version='latest')


# pylint:disable=redefined-outer-name
@pytest.fixture(scope='session')
def docker_image(docker_repository, docker_image_tag):

    # if IS_BUILDKITE:
    return '{repository}/{image}:{tag}'.format(
        repository=docker_repository, image=DOCKER_IMAGE_NAME, tag=docker_image_tag
    )


@pytest.fixture(scope='session')
def cluster(cluster_name):  # pylint: disable=redefined-outer-name
    try:
        print('--- \033[32m:k8s: Running kind cluster setup\033[0m')
        subprocess.check_call(['kind', 'create', 'cluster', '--name', cluster_name])
        yield cluster_name
    finally:
        # ensure cleanup happens on error or normal exit
        subprocess.check_call('kind delete cluster --name %s' % cluster_name, shell=True)


@pytest.fixture(scope='session')
def kubeconfig(cluster):  # pylint: disable=redefined-outer-name
    old_kubeconfig = os.getenv('KUBECONFIG')
    try:
        print('Writing kubeconfig to file %s' % KUBECONFIG_FILE)
        if not IS_BUILDKITE and sys.platform == 'darwin':
            kubeconfig_call = 'kind get kubeconfig --name {cluster_name}'.format(
                cluster_name=cluster
            )
        else:
            kubeconfig_call = 'kind get kubeconfig --internal --name {cluster_name}'.format(
                cluster_name=cluster
            )

        with open(KUBECONFIG_FILE, 'wb') as f:
            subprocess.check_call(
                kubeconfig_call, stdout=f, shell=True,
            )
        os.environ['KUBECONFIG'] = KUBECONFIG_FILE

        yield KUBECONFIG_FILE

    finally:
        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        if old_kubeconfig is not None:
            os.environ['KUBECONFIG'] = old_kubeconfig


@pytest.fixture(scope='session')
def kind_cluster(
    cluster, kubeconfig, docker_image,  # docker_job_image_repository
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
        subprocess.check_call(['kind', 'load', 'docker-image', '--name', cluster, docker_image])
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
    kind_cluster, docker_image_tag, docker_repository,  # docker_job_image_repository,
):  # pylint: disable=redefined-outer-name,unused-argument
    print('--- \033[32m:helm: Installing Helm chart\033[0m"')

    # Install helm chart
    subprocess.check_call(
        '''helm install \
    --set dagit.image.repository="{repository}/{image}" \\
    --set dagit.image.tag="{tag}" \\
    --set job_image.image.repository="{repository}/{image}" \\
    --set job_image.image.tag="{tag}" \\
    dagster \\
    helm/dagster/'''.format(
            image=DOCKER_IMAGE_NAME, tag=docker_image_tag, repository=docker_repository,
        ),
        shell=True,
        cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
    )
    success, _ = wait_for_pod('dagit')
    assert success
    yield


@pytest.fixture(scope='session')
def run_launcher(helm_chart, docker_image):  # pylint: disable=redefined-outer-name,unused-argument
    return K8sRunLauncher(
        postgres_host='dagster-postgresql',
        postgres_port='5432',
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        instance_config_map='dagster-instance',
        job_image=docker_image,
        load_kubeconfig=True,
        kubeconfig_file=KUBECONFIG_FILE,
    )
