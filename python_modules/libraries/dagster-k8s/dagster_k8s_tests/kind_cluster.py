import os
import subprocess
import uuid
from contextlib import contextmanager

from kubernetes import client, config

from dagster import check
from dagster.utils import safe_tempfile_path

from .utils import check_output, which_, within_docker


def kind_cluster_exists(cluster_name):
    running_clusters = check_output(['kind', 'get', 'clusters']).decode('utf-8').split('\n')
    cluster_exists = cluster_name in running_clusters
    return cluster_exists


@contextmanager
def create_kind_cluster(cluster_name, keep_cluster=False):
    check.str_param(cluster_name, 'cluster_name')
    check.bool_param(keep_cluster, 'keep_cluster')

    try:
        print(
            '--- \033[32m:k8s: Running kind cluster setup for cluster '
            '{cluster_name}\033[0m'.format(cluster_name=cluster_name)
        )
        check_output(['kind', 'create', 'cluster', '--name', cluster_name])
        yield cluster_name

    finally:
        # ensure cleanup happens on error or normal exit
        if not keep_cluster:
            print('--- Cleaning up kind cluster {cluster_name}'.format(cluster_name=cluster_name))
            check_output(['kind', 'delete', 'cluster', '--name', cluster_name])


@contextmanager
def kind_kubeconfig(cluster_name, use_internal_address=True):
    '''For kind clusters, we need to write our own kubeconfig file to leave the user's existing
    kubeconfig alone
    '''
    check.str_param(cluster_name, 'cluster_name')
    check.bool_param(use_internal_address, 'use_internal_address')

    old_kubeconfig = os.getenv('KUBECONFIG')
    try:
        kubeconfig_call = ['kind', 'get', 'kubeconfig', '--name', cluster_name]
        if use_internal_address:
            kubeconfig_call += ['--internal']

        with safe_tempfile_path() as kubeconfig_file:
            print('Writing kubeconfig to file %s' % kubeconfig_file)

            with open(kubeconfig_file, 'wb') as f:
                subprocess.check_call(kubeconfig_call, stdout=f)

            os.environ['KUBECONFIG'] = kubeconfig_file

            yield kubeconfig_file

    finally:
        print('Cleaning up kubeconfig')
        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        if old_kubeconfig is not None:
            os.environ['KUBECONFIG'] = old_kubeconfig


def kind_sync_dockerconfig():
    '''Copies docker config to kind cluster node(s) for private registry auth.

    See: https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
    '''
    print('--- Syncing docker config to nodes...')

    # https://github.com/kubernetes-client/python/issues/895#issuecomment-515025300
    from kubernetes.client.models.v1_container_image import V1ContainerImage

    def names(self, names):
        self._names = names  # pylint: disable=protected-access

    V1ContainerImage.names = V1ContainerImage.names.setter(names)  # pylint: disable=no-member

    nodes = client.CoreV1Api().list_node().items
    for node in nodes:
        node_name = node.metadata.name

        docker_exe = which_('docker')

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


@contextmanager
def kind_cluster(cluster_name=None, keep_cluster=False):
    cluster_name = cluster_name or 'cluster-{uuid}'.format(uuid=uuid.uuid4().hex)

    if kind_cluster_exists(cluster_name):
        yield cluster_name

        if not keep_cluster:
            print(
                "WARNING: keep_cluster is false, won't delete your existing cluster. If you'd "
                "like to delete this cluster, please manually remove by running the command:\n\n"
                "kind delete cluster --name %s" % cluster_name
            )
    else:
        # We need to use an internal address in a DinD context like Buildkite
        use_internal_address = within_docker()

        with create_kind_cluster(cluster_name, keep_cluster=keep_cluster):
            with kind_kubeconfig(cluster_name, use_internal_address) as kubeconfig_file:
                config.load_kube_config(config_file=kubeconfig_file)
                kind_sync_dockerconfig()
                yield cluster_name, kubeconfig_file
