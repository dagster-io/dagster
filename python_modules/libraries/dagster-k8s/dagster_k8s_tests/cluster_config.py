from collections import namedtuple

from dagster import check


class ClusterConfig(namedtuple('_ClusterConfig', 'name kubeconfig_file')):
    '''Used to represent a cluster, returned by the cluster_provider fixture below.
    '''

    def __new__(cls, name, kubeconfig_file):
        return super(ClusterConfig, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            kubeconfig_file=check.str_param(kubeconfig_file, 'kubeconfig_file'),
        )
