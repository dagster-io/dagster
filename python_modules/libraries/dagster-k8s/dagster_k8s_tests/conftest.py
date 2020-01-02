import os
import subprocess
import uuid

import pytest
import six
from dagster_k8s.launcher import K8sRunLauncher
from kubernetes import client, config

from dagster.utils import script_relative_path

from .utils import wait_for_pod

TOX_PYTHON_VERSION = 'py37'

KUBECONFIG_FILE = '/tmp/kubeconfig'


@pytest.fixture(scope='session')
def docker_repository():
    assert (
        'DAGSTER_DOCKER_REPOSITORY' in os.environ
    ), 'This test requires the environment variable DAGSTER_DOCKER_REPOSITORY to be set to proceed'

    return os.environ['DAGSTER_DOCKER_REPOSITORY']


@pytest.fixture(scope='session')
def docker_image_name():
    return 'dagster-docker-buildkite'


@pytest.fixture(scope='session')
def docker_image_tag():
    assert (
        'DAGSTER_DOCKER_IMAGE_TAG' in os.environ
    ), 'This test requires the environment variable DAGSTER_DOCKER_IMAGE_TAG to be set to proceed'

    return os.environ['DAGSTER_DOCKER_IMAGE_TAG']


@pytest.fixture(scope='session')
def docker_image(
    docker_repository, docker_image_name, docker_image_tag
):  # pylint: disable=redefined-outer-name
    return '{repository}/{image}:{tag}'.format(
        repository=docker_repository, image=docker_image_name, tag=docker_image_tag
    )


@pytest.fixture(scope='session')
def git_repository_root():
    return six.ensure_str(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip())


@pytest.fixture(scope='session')
def test_repo_path(git_repository_root):  # pylint: disable=redefined-outer-name
    return script_relative_path(
        os.path.join(git_repository_root, '.buildkite', 'images', 'docker', 'test_project')
    )


@pytest.fixture(scope='session')
def environments_path(test_repo_path):  # pylint: disable=redefined-outer-name
    return os.path.join(test_repo_path, 'test_pipelines', 'environments')


@pytest.fixture(scope='session')
def kind_cluster():
    # Need a unique cluster name for this job; can't have hyphens
    cluster_name = 'kindcluster{uuid}'.format(uuid=uuid.uuid4().hex)

    try:
        print('--- \033[32m:k8s: Running kind cluster setup\033[0m')
        subprocess.check_call('kind create cluster --name %s' % cluster_name, shell=True)

        print('Writing kubeconfig to file %s' % KUBECONFIG_FILE)
        with open(KUBECONFIG_FILE, 'wb') as f:
            subprocess.check_call(
                'kind get kubeconfig --internal --name %s' % cluster_name, stdout=f, shell=True,
            )
        os.environ['KUBECONFIG'] = KUBECONFIG_FILE

        print('Installing ECR credentials...')
        subprocess.check_call(
            'aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True
        )

        # see https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
        print('Syncing to nodes...')
        config.load_kube_config(KUBECONFIG_FILE)
        nodes = client.CoreV1Api().list_node().items
        for node in nodes:
            node_name = node.metadata.name

            # copy the config to where kubelet will look
            cmd = os.path.expandvars(
                '/usr/bin/docker cp $HOME/.docker/config.json '
                '{node_name}:/var/lib/kubelet/config.json'.format(node_name=node_name)
            )
            subprocess.check_call(cmd, shell=True)

            # restart kubelet to pick up the config
            print('Restarting node kubelets...')
            subprocess.check_call(
                'docker exec %s systemctl restart kubelet.service' % node_name, shell=True
            )

        yield cluster_name

    finally:
        # ensure cleanup happens on error or normal exit
        subprocess.check_call('kind delete cluster --name %s' % cluster_name, shell=True)

        # clean up kubeconfig
        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']


@pytest.fixture(scope='session')
def helm_chart(
    kind_cluster, git_repository_root, docker_repository, docker_image_name, docker_image_tag
):  # pylint: disable=redefined-outer-name,unused-argument
    print('--- \033[32m:helm: Installing Helm chart\033[0m"')

    # Install helm chart
    subprocess.check_call(
        '''helm install \
    --set dagit.image.repository="{repository}/{image}" \\
    --set dagit.image.tag="{tag}" \\
    --set job_image.image.repository="{repository}" \\
    --set job_image.image.tag="{tag}" \\
    dagster \\
    helm/dagster/'''.format(
            repository=docker_repository, image=docker_image_name, tag=docker_image_tag
        ),
        shell=True,
        cwd=os.path.join(git_repository_root, 'python_modules/libraries/dagster-k8s/'),
    )
    wait_for_pod('dagit')
    yield


@pytest.fixture(scope='session')
def run_launcher(helm_chart, docker_image):  # pylint: disable=redefined-outer-name,unused-argument
    return K8sRunLauncher(
        postgres_host='dagster-postgresql',
        postgres_port='5432',
        image_pull_secrets=[{'name': 'element-dev-key'}],
        service_account_name='dagit-admin',
        job_image=docker_image,
        load_kubeconfig=True,
        kubeconfig_file=KUBECONFIG_FILE,
    )
