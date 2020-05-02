import os
import random
import socket
import subprocess
from contextlib import closing

import six
from dagster_graphql.client.util import parse_raw_log_lines
from dagster_k8s.utils import get_pod_names_in_job, retrieve_pod_logs, wait_for_job_success

from dagster import check

IS_BUILDKITE = os.getenv('BUILDKITE') is not None


def image_pull_policy():
    # This is because when running local tests, we need to load the image into the kind cluster (and
    # then not attempt to pull it) because we don't want to require credentials for a private
    # registry / pollute the private registry / set up and network a local registry as a condition
    # of running tests
    if IS_BUILDKITE:
        return 'Always'
    else:
        return 'IfNotPresent'


def get_test_namespace():
    namespace_suffix = hex(random.randint(0, 16 ** 6))[2:]
    return 'dagster-test-%s' % namespace_suffix


def within_docker():
    '''detect if we're running inside of a docker container

    from: https://stackoverflow.com/a/48710609/11295366
    '''
    cgroup_path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv')
        or os.path.isfile(cgroup_path)
        and any('docker' in line for line in open(cgroup_path))
    )


def which_(exe):
    '''Uses distutils to look for an executable, mimicking unix which'''
    from distutils import spawn  # pylint: disable=no-name-in-module

    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


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


def remove_none_recursively(obj):
    '''Remove none values from a dict. This is used here to support comparing provided config vs.
    config we retrive from kubernetes, which returns all fields, even those which have no value
    configured.
    '''
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none_recursively(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none_recursively(k), remove_none_recursively(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj


def wait_for_job_and_get_logs(job_name, namespace):
    '''Wait for a dagster-k8s job to complete, ensure it launched only one pod,
    and then grab the logs from the pod it launched.
    '''
    check.str_param(job_name, 'job_name')
    check.str_param(namespace, 'namespace')

    wait_for_job_success(job_name, namespace=namespace)

    pod_names = get_pod_names_in_job(job_name, namespace)

    assert len(pod_names) == 1

    pod_name = pod_names[0]

    raw_logs = retrieve_pod_logs(pod_name, namespace=namespace)
    return parse_raw_log_lines(raw_logs.split('\n'))
