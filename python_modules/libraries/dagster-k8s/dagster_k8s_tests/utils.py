import os
import socket
import subprocess
import time
from contextlib import closing

import six
from kubernetes import client


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


def retrieve_pod_logs(pod_name):
    '''Retrieves the raw pod logs for the pod named `pod_name` from Kubernetes.
    '''
    # We set _preload_content to False here to prevent the k8 python api from processing the response.
    # If the logs happen to be JSON - it will parse in to a dict and then coerce back to a str
    # leaving us with invalid JSON as the quotes have been switched to '
    #
    # https://github.com/kubernetes-client/python/issues/811
    raw_logs = (
        client.CoreV1Api()
        .read_namespaced_pod_log(name=pod_name, namespace='dagster-test', _preload_content=False,)
        .data
    ).decode('utf-8')

    return raw_logs


def wait_for_job_success(job_name):
    '''Poll the job for successful completion
    '''
    job = None
    while not job:
        # Ensure we found the job that we launched
        jobs = client.BatchV1Api().list_namespaced_job(namespace='dagster-test', watch=False)
        job = next((j for j in jobs.items if j.metadata.name == job_name), None)
        print('Job not yet launched, waiting')
        time.sleep(1)

    success, job_pod_name = wait_for_pod(job.metadata.name, wait_for_termination=True)

    raw_logs = retrieve_pod_logs(job_pod_name)

    return success, raw_logs


def wait_for_pod(
    name,
    wait_for_termination=False,
    wait_for_readiness=False,
    timeout=600.0,
    namespace='dagster-test',
):
    '''Wait for the dagit pod to launch and be running, or wait for termination

    NOTE: Adding this wait because helm --wait will just wait indefinitely in a crash loop scenario,
    whereas we want to catch that, fail the test, and alert the user. We also need to ensure the
    Helm chart is fully launched before we launch the tox tests.
    '''
    print('--- \033[32m:k8s: Waiting for pod %s\033[0m' % name)

    success = True

    start = time.time()

    while True:
        pods = client.CoreV1Api().list_namespaced_pod(namespace=namespace)
        pod = next((p for p in pods.items if name in p.metadata.name), None)

        if time.time() - start > timeout:
            raise Exception('Timed out while waiting for pod to become ready; pod info: ', pod)

        if pod is None:
            print('Waiting for pod "%s" to launch...' % name)
            time.sleep(1)
            continue

        if not pod.status.container_statuses:
            print('Waiting for pod container status to be set by kubernetes...')
            time.sleep(1)
            continue

        state = pod.status.container_statuses[0].state
        ready = pod.status.container_statuses[0].ready

        if state.running is not None:
            if wait_for_readiness:
                if not ready:
                    print('Waiting for pod to become ready...')
                    time.sleep(1)
                    continue
                else:
                    break
            if wait_for_termination:
                time.sleep(1)
                continue
            break

        elif state.waiting is not None:
            if state.waiting.reason == 'PodInitializing':
                print('Waiting for pod to initialize...')
                time.sleep(1)
                continue
            elif state.waiting.reason == 'ContainerCreating':
                print('Waiting for container creation...')
                time.sleep(1)
                continue
            elif state.waiting.reason in [
                'ErrImagePull',
                'ImagePullBackOff',
                'CrashLoopBackOff',
                'RunContainerError',
            ]:
                print('Failed: %s' % state.waiting.message)
                success = False
                break
            else:
                print('Unknown issue: %s' % state.waiting)
                success = False
                break

        elif state.terminated is not None:
            if not state.terminated.exit_code == 0:
                print(
                    'Pod did not exit successfully. Failed with message: %s'
                    % state.terminated.message
                )
                success = False
                raw_logs = retrieve_pod_logs(name)
                print('Pod logs: ', raw_logs)
            break

        else:
            print('Should not get here, unknown pod state')
            success = False
            break

    return success, pod.metadata.name
