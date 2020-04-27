import os
from collections import namedtuple

import kubernetes
import pytest

from dagster import check

from .utils import IS_BUILDKITE, check_output


class ClusterConfig(namedtuple('_ClusterConfig', 'name kubeconfig_file')):
    '''Used to represent a cluster, returned by the cluster_provider fixture below.
    '''

    def __new__(cls, name, kubeconfig_file):
        return super(ClusterConfig, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            kubeconfig_file=check.str_param(kubeconfig_file, 'kubeconfig_file'),
        )


def define_cluster_provider_fixture(additional_kind_images=None):
    @pytest.fixture(scope='session')
    def _cluster_provider(request):
        from .kind import kind_cluster_exists, kind_cluster, kind_load_images
        from .test_project import build_and_tag_test_image, test_project_docker_image

        if IS_BUILDKITE:
            print('Installing ECR credentials...')
            check_output('aws ecr get-login --no-include-email --region us-west-1 | sh', shell=True)

        provider = request.config.getoption('--cluster-provider')

        # Use a kind cluster
        if provider == 'kind':
            cluster_name = request.config.getoption('--kind-cluster')

            # Cluster will be deleted afterwards unless this is set.
            # This is to allow users to reuse an existing cluster in local test by running
            # `pytest --kind-cluster my-cluster --no-cleanup` -- this avoids the per-test run
            # overhead of cluster setup and teardown
            should_cleanup = not request.config.getoption('--no-cleanup')

            existing_cluster = kind_cluster_exists(cluster_name)

            with kind_cluster(cluster_name, should_cleanup=should_cleanup) as cluster_config:
                if not IS_BUILDKITE and not existing_cluster:
                    docker_image = test_project_docker_image()
                    build_and_tag_test_image(docker_image)
                    kind_load_images(
                        cluster_name=cluster_config.name,
                        local_dagster_test_image=docker_image,
                        additional_images=additional_kind_images,
                    )
                yield cluster_config

        # Use cluster from kubeconfig
        elif provider == 'kubeconfig':
            kubeconfig_file = os.getenv('KUBECONFIG', os.path.expandvars('${HOME}/.kube/config'))
            kubernetes.config.load_kube_config(config_file=kubeconfig_file)
            yield ClusterConfig(name='from_system_kubeconfig', kubeconfig_file=kubeconfig_file)

        else:
            raise Exception('unknown cluster provider %s' % provider)

    return _cluster_provider
