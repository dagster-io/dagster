import base64
import os
import subprocess
import time
from contextlib import contextmanager

import kubernetes
import six
import yaml
from dagster_k8s.utils import wait_for_pod

from dagster import check
from dagster.utils import git_repository_root

from .utils import check_output, get_test_namespace


@contextmanager
def test_namespace(should_cleanup=True):
    # Will be something like dagster-test-3fcd70 to avoid ns collisions in shared test environment
    namespace = get_test_namespace()

    print('--- \033[32m:k8s: Creating test namespace %s\033[0m' % namespace)
    kube_api = kubernetes.client.CoreV1Api()

    try:
        print('Creating namespace %s' % namespace)
        kube_namespace = kubernetes.client.V1Namespace(
            metadata=kubernetes.client.V1ObjectMeta(name=namespace)
        )
        kube_api.create_namespace(kube_namespace)
        yield namespace

    finally:
        # Can skip this step as a time saver when we're going to destroy the cluster anyway, e.g.
        # w/ a kind cluster
        if should_cleanup:
            print('Deleting namespace %s' % namespace)
            kube_api.delete_namespace(name=namespace)


@contextmanager
def helm_test_resources(namespace, should_cleanup=True):
    '''Create a couple of resources to test Helm interaction w/ pre-existing resources.
    '''
    check.str_param(namespace, 'namespace')
    check.bool_param(should_cleanup, 'should_cleanup')

    try:
        print('Creating k8s test objects ConfigMap test-env-configmap and Secret test-env-secret')
        kube_api = kubernetes.client.CoreV1Api()

        configmap = kubernetes.client.V1ConfigMap(
            api_version='v1',
            kind='ConfigMap',
            data={'TEST_ENV_VAR': 'foobar'},
            metadata=kubernetes.client.V1ObjectMeta(name='test-env-configmap'),
        )
        kube_api.create_namespaced_config_map(namespace=namespace, body=configmap)

        # Secret values are expected to be base64 encoded
        secret_val = six.ensure_str(base64.b64encode(six.ensure_binary('foobar')))
        secret = kubernetes.client.V1Secret(
            api_version='v1',
            kind='Secret',
            data={'TEST_SECRET_ENV_VAR': secret_val},
            metadata=kubernetes.client.V1ObjectMeta(name='test-env-secret'),
        )
        kube_api.create_namespaced_secret(namespace=namespace, body=secret)

        yield

    finally:
        # Can skip this step as a time saver when we're going to destroy the cluster anyway, e.g.
        # w/ a kind cluster
        if should_cleanup:
            kube_api.delete_namespaced_config_map(name='test-env-configmap', namespace=namespace)
            kube_api.delete_namespaced_secret(name='test-env-secret', namespace=namespace)


@contextmanager
def helm_chart(namespace, image_pull_policy, docker_image, should_cleanup=True):
    '''Install dagster-k8s helm chart.
    '''
    check.str_param(namespace, 'namespace')
    check.str_param(image_pull_policy, 'image_pull_policy')
    check.str_param(docker_image, 'docker_image')
    check.bool_param(should_cleanup, 'should_cleanup')

    print('--- \033[32m:helm: Installing Helm chart\033[0m')

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
            namespace,
            '-f',
            '-',
            'dagster',
            'helm/dagster/',
        ]

        print('Running Helm Install: \n', ' '.join(helm_cmd), '\nWith config:\n', helm_config_yaml)

        p = subprocess.Popen(
            helm_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate(six.ensure_binary(helm_config_yaml))
        print('\n\nHelm install stdout:\n', six.ensure_str(stdout))
        print('\n\nHelm install stderr:\n', six.ensure_str(stderr))
        assert p.returncode == 0

        check_output(
            helm_cmd,
            shell=True,
            cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
        )

        # Wait for Dagit pod to be ready (won't actually stay up w/out js rebuild)
        kube_api = kubernetes.client.CoreV1Api()

        print('Waiting for Dagit pod to be ready...')
        dagit_pod = None
        while dagit_pod is None:
            pods = kube_api.list_namespaced_pod(namespace=namespace)
            pod_names = [p.metadata.name for p in pods.items if 'dagit' in p.metadata.name]
            if pod_names:
                dagit_pod = pod_names[0]
            time.sleep(1)

        # Wait for additional Celery worker queues to become ready
        pods = kubernetes.client.CoreV1Api().list_namespaced_pod(namespace=namespace)
        for extra_queue in helm_config['celery']['extraWorkerQueues']:
            pod_names = [
                p.metadata.name for p in pods.items if extra_queue['name'] in p.metadata.name
            ]
            assert len(pod_names) == extra_queue['replicaCount']
            for pod in pod_names:
                print('Waiting for pod %s' % pod)
                wait_for_pod(pod, namespace=namespace)

        yield

    finally:
        # Can skip this step as a time saver when we're going to destroy the cluster anyway, e.g.
        # w/ a kind cluster
        if should_cleanup:
            print('Uninstalling helm chart')
            check_output(
                ['helm', 'uninstall', 'dagster', '--namespace', namespace],
                shell=True,
                cwd=os.path.join(git_repository_root(), 'python_modules/libraries/dagster-k8s/'),
            )
