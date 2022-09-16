import logging
import sys
import time
from enum import Enum
from typing import Optional

import kubernetes

from dagster import DagsterInstance
from dagster import _check as check
from dagster._core.storage.pipeline_run import PipelineRunStatus

DEFAULT_WAIT_TIMEOUT = 86400.0  # 1 day
DEFAULT_WAIT_BETWEEN_ATTEMPTS = 10.0  # 10 seconds
DEFAULT_JOB_POD_COUNT = 1  # expect job:pod to be 1:1 by default


class WaitForPodState(Enum):
    Ready = "READY"
    Terminated = "TERMINATED"


class DagsterK8sError(Exception):
    pass


class DagsterK8sTimeoutError(DagsterK8sError):
    pass


class DagsterK8sAPIRetryLimitExceeded(Exception):
    def __init__(self, *args, **kwargs):
        k8s_api_exception = check.inst_param(
            kwargs.pop("k8s_api_exception"), "k8s_api_exception", Exception
        )
        original_exc_info = check.tuple_param(kwargs.pop("original_exc_info"), "original_exc_info")
        max_retries = check.int_param(kwargs.pop("max_retries"), "max_retries")

        check.invariant(original_exc_info[0] is not None)
        super(DagsterK8sAPIRetryLimitExceeded, self).__init__(
            f"Retry limit of {max_retries} exceeded: " + args[0],
            *args[1:],
            **kwargs,
        )

        self.k8s_api_exception = check.opt_inst_param(
            k8s_api_exception, "k8s_api_exception", Exception
        )
        self.original_exc_info = original_exc_info


class DagsterK8sUnrecoverableAPIError(Exception):
    def __init__(self, *args, **kwargs):
        k8s_api_exception = check.inst_param(
            kwargs.pop("k8s_api_exception"), "k8s_api_exception", Exception
        )
        original_exc_info = check.tuple_param(kwargs.pop("original_exc_info"), "original_exc_info")

        check.invariant(original_exc_info[0] is not None)
        super(DagsterK8sUnrecoverableAPIError, self).__init__(args[0], *args[1:], **kwargs)

        self.k8s_api_exception = check.opt_inst_param(
            k8s_api_exception, "k8s_api_exception", Exception
        )
        self.original_exc_info = original_exc_info


class DagsterK8sPipelineStatusException(Exception):
    pass


WHITELISTED_TRANSIENT_K8S_STATUS_CODES = [
    503,  # Service unavailable
    504,  # Gateway timeout
    500,  # Internal server error
]


def k8s_api_retry(
    fn,
    max_retries,
    timeout,
    msg_fn=lambda: "Unexpected error encountered in Kubernetes API Client.",
):
    check.callable_param(fn, "fn")
    check.int_param(max_retries, "max_retries")
    check.numeric_param(timeout, "timeout")

    remaining_attempts = 1 + max_retries
    while remaining_attempts > 0:
        remaining_attempts -= 1

        try:
            return fn()
        except kubernetes.client.rest.ApiException as e:
            # Only catch whitelisted ApiExceptions
            status = e.status

            # Check if the status code is generally whitelisted
            whitelisted = status in WHITELISTED_TRANSIENT_K8S_STATUS_CODES

            # If there are remaining attempts, swallow the error
            if whitelisted and remaining_attempts > 0:
                time.sleep(timeout)
            elif whitelisted and remaining_attempts == 0:
                raise DagsterK8sAPIRetryLimitExceeded(
                    msg_fn(),
                    k8s_api_exception=e,
                    max_retries=max_retries,
                    original_exc_info=sys.exc_info(),
                ) from e
            else:
                raise DagsterK8sUnrecoverableAPIError(
                    msg_fn(),
                    k8s_api_exception=e,
                    original_exc_info=sys.exc_info(),
                ) from e


class KubernetesWaitingReasons:
    PodInitializing = "PodInitializing"
    ContainerCreating = "ContainerCreating"
    ErrImagePull = "ErrImagePull"
    ImagePullBackOff = "ImagePullBackOff"
    CrashLoopBackOff = "CrashLoopBackOff"
    RunContainerError = "RunContainerError"
    CreateContainerConfigError = "CreateContainerConfigError"


class DagsterKubernetesClient:
    def __init__(self, batch_api, core_api, logger, sleeper, timer):
        self.batch_api = batch_api
        self.core_api = core_api
        self.logger = logger
        self.sleeper = sleeper
        self.timer = timer

    @staticmethod
    def production_client():
        return DagsterKubernetesClient(
            kubernetes.client.BatchV1Api(),
            kubernetes.client.CoreV1Api(),
            logging.info,
            time.sleep,
            time.time,
        )

    ### Job operations ###

    def wait_for_job(
        self,
        job_name,
        namespace,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
        start_time=None,
    ):
        """Wait for a job to launch and be running.

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT. Set to 0 to disable.
            wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
                to DEFAULT_WAIT_BETWEEN_ATTEMPTS.

        Raises:
            DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")
        check.numeric_param(wait_timeout, "wait_timeout")
        check.numeric_param(wait_time_between_attempts, "wait_time_between_attempts")

        job = None
        start = start_time or self.timer()

        while not job:
            if wait_timeout and (self.timer() - start > wait_timeout):
                raise DagsterK8sTimeoutError(
                    "Timed out while waiting for job {job_name}"
                    " to launch".format(job_name=job_name)
                )

            # Get all jobs in the namespace and find the matching job
            def _get_jobs_for_namespace():
                jobs = self.batch_api.list_namespaced_job(
                    namespace=namespace, field_selector="metadata.name={}".format(job_name)
                )
                if jobs.items:
                    check.invariant(
                        len(jobs.items) == 1,
                        'There should only be one k8s job with name "{}", but got multiple jobs:" {}'.format(
                            job_name, jobs.items
                        ),
                    )
                    return jobs.items[0]
                else:
                    return None

            job = k8s_api_retry(
                _get_jobs_for_namespace, max_retries=3, timeout=wait_time_between_attempts
            )

            if not job:
                self.logger('Job "{job_name}" not yet launched, waiting'.format(job_name=job_name))
                self.sleeper(wait_time_between_attempts)

    def wait_for_job_to_have_pods(
        self,
        job_name,
        namespace,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=5,
        start_time=None,
    ):
        start = start_time or self.timer()

        def _get_pods():
            return self.get_pods_in_job(job_name, namespace)

        while True:
            if wait_timeout and (self.timer() - start > wait_timeout):
                raise DagsterK8sTimeoutError(
                    "Timed out while waiting for job {job_name}"
                    " to have pods".format(job_name=job_name)
                )

            pod_list = k8s_api_retry(_get_pods, max_retries=3, timeout=wait_time_between_attempts)

            if pod_list:
                return pod_list

            self.logger(
                'Job "{job_name}" does not yet have pods, waiting'.format(job_name=job_name)
            )
            self.sleeper(wait_time_between_attempts)

    def wait_for_job_success(
        self,
        job_name,
        namespace,
        instance=None,
        run_id=None,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
        num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
    ):
        """Poll a job for successful completion.

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT. Set to 0 to disable.
            wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
                to DEFAULT_WAIT_BETWEEN_ATTEMPTS.

        Raises:
            DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")
        check.opt_inst_param(instance, "instance", DagsterInstance)
        check.opt_str_param(run_id, "run_id")
        check.numeric_param(wait_timeout, "wait_timeout")
        check.numeric_param(wait_time_between_attempts, "wait_time_between_attempts")
        check.int_param(num_pods_to_wait_for, "num_pods_to_wait_for")

        start = self.timer()

        # Wait for job to be running
        self.wait_for_job(
            job_name,
            namespace,
            wait_timeout=wait_timeout,
            wait_time_between_attempts=wait_time_between_attempts,
            start_time=start,
        )

        self.wait_for_running_job_to_succeed(
            job_name,
            namespace,
            instance,
            run_id,
            wait_timeout,
            wait_time_between_attempts,
            num_pods_to_wait_for,
            start_time=start,
        )

    def wait_for_running_job_to_succeed(
        self,
        job_name,
        namespace,
        instance=None,
        run_id=None,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
        num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
        start_time: Optional[float] = None,
    ):
        if wait_timeout:
            check.float_param(start_time, "start_time")

        # Wait for the job status to be completed. We check the status every
        # wait_time_between_attempts seconds
        while True:
            if wait_timeout and (self.timer() - start_time > wait_timeout):
                raise DagsterK8sTimeoutError(
                    "Timed out while waiting for job {job_name}"
                    " to complete".format(job_name=job_name)
                )

            # Reads the status of the specified job. Returns a V1Job object that
            # we need to read the status off of.
            status = None

            def _get_job_status():
                job = self.batch_api.read_namespaced_job_status(job_name, namespace=namespace)
                return job.status

            status = k8s_api_retry(
                _get_job_status, max_retries=3, timeout=wait_time_between_attempts
            )

            # status.succeeded represents the number of pods which reached phase Succeeded.
            if status.succeeded == num_pods_to_wait_for:
                break

            # status.failed represents the number of pods which reached phase Failed.
            if status.failed and status.failed > 0:
                raise DagsterK8sError(
                    "Encountered failed job pods for job {job_name} with status: {status}, "
                    "in namespace {namespace}".format(
                        job_name=job_name, status=status, namespace=namespace
                    )
                )

            if instance and run_id:
                pipeline_run = instance.get_run_by_id(run_id)
                if not pipeline_run:
                    raise DagsterK8sPipelineStatusException()

                pipeline_run_status = pipeline_run.status
                if pipeline_run_status != PipelineRunStatus.STARTED:
                    raise DagsterK8sPipelineStatusException()

            self.sleeper(wait_time_between_attempts)

    def delete_job(
        self,
        job_name,
        namespace,
    ):
        """Delete Kubernetes Job. We also need to delete corresponding pods due to:
        https://github.com/kubernetes-client/python/issues/234

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")

        try:
            pod_names = self.get_pod_names_in_job(job_name, namespace)

            # Collect all the errors so that we can post-process before raising
            pod_names = self.get_pod_names_in_job(job_name, namespace)

            errors = []
            try:
                self.batch_api.delete_namespaced_job(name=job_name, namespace=namespace)
            except Exception as e:
                errors.append(e)

            for pod_name in pod_names:
                try:
                    self.core_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
                except Exception as e:
                    errors.append(e)

            if len(errors) > 0:
                # Raise first non-expected error. Else, raise first error.
                for error in errors:
                    if not (
                        isinstance(error, kubernetes.client.rest.ApiException)
                        and error.reason == "Not Found"
                    ):
                        raise error
                raise errors[0]

            return True
        except kubernetes.client.rest.ApiException as e:
            if e.reason == "Not Found":
                return False
            raise e

    ### Pod operations ###

    def get_pods_in_job(self, job_name, namespace):
        """Get the pods launched by the job ``job_name``.

        Args:
            job_name (str): Name of the job to inspect.
            namespace (str): Namespace in which the job is located.

        Returns:
            List[V1Pod]: List of all pod objects that have been launched by the job ``job_name``.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")

        return self.core_api.list_namespaced_pod(
            namespace=namespace, label_selector="job-name={}".format(job_name)
        ).items

    def get_pod_names_in_job(self, job_name, namespace):
        """Get the names of pods launched by the job ``job_name``.

        Args:
            job_name (str): Name of the job to inspect.
            namespace (str): Namespace in which the job is located.

        Returns:
            List[str]: List of all pod names that have been launched by the job ``job_name``.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")

        pods = self.get_pods_in_job(job_name, namespace)
        return [p.metadata.name for p in pods]

    def wait_for_pod(
        self,
        pod_name,
        namespace,
        wait_for_state=WaitForPodState.Ready,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
        start_time=None,
    ):
        """Wait for a pod to launch and be running, or wait for termination (useful for job pods).

        Args:
            pod_name (str): Name of the pod to wait for.
            namespace (str): Namespace in which the pod is located.
            wait_for_state (WaitForPodState, optional): Whether to wait for pod readiness or
                termination. Defaults to waiting for readiness.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT. Set to 0 to disable.
            wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
                to DEFAULT_WAIT_BETWEEN_ATTEMPTS.

        Raises:
            DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered
        """
        check.str_param(pod_name, "pod_name")
        check.str_param(namespace, "namespace")
        check.inst_param(wait_for_state, "wait_for_state", WaitForPodState)
        check.numeric_param(wait_timeout, "wait_timeout")
        check.numeric_param(wait_time_between_attempts, "wait_time_between_attempts")

        self.logger('Waiting for pod "%s"' % pod_name)

        start = start_time or self.timer()

        while True:

            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, field_selector="metadata.name=%s" % pod_name
            ).items
            pod = pods[0] if pods else None

            if wait_timeout and self.timer() - start > wait_timeout:
                raise DagsterK8sError(
                    "Timed out while waiting for pod to become ready with pod info: %s" % str(pod)
                )

            if pod is None:
                self.logger('Waiting for pod "%s" to launch...' % pod_name)
                self.sleeper(wait_time_between_attempts)
                continue

            if not pod.status.container_statuses:
                self.logger("Waiting for pod container status to be set by kubernetes...")
                self.sleeper(wait_time_between_attempts)
                continue

            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstatus-v1-core
            container_status = pod.status.container_statuses[0]

            # State checks below, see:
            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstate-v1-core
            state = container_status.state

            if state.running is not None:
                if wait_for_state == WaitForPodState.Ready:
                    # ready is boolean field of container status
                    ready = container_status.ready
                    if not ready:
                        self.logger('Waiting for pod "%s" to become ready...' % pod_name)
                        self.sleeper(wait_time_between_attempts)
                        continue
                    else:
                        self.logger('Pod "%s" is ready, done waiting' % pod_name)
                        break
                else:
                    check.invariant(
                        wait_for_state == WaitForPodState.Terminated, "New invalid WaitForPodState"
                    )
                    self.sleeper(wait_time_between_attempts)
                    continue

            elif state.waiting is not None:
                # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstatewaiting-v1-core
                if state.waiting.reason == KubernetesWaitingReasons.PodInitializing:
                    self.logger('Waiting for pod "%s" to initialize...' % pod_name)
                    self.sleeper(wait_time_between_attempts)
                    continue
                if state.waiting.reason == KubernetesWaitingReasons.CreateContainerConfigError:
                    self.logger(
                        'Pod "%s" is waiting due to a CreateContainerConfigError with message "%s" - trying again to see if it recovers'
                        % (pod_name, state.waiting.message)
                    )
                    self.sleeper(wait_time_between_attempts)
                    continue
                elif state.waiting.reason == KubernetesWaitingReasons.ContainerCreating:
                    self.logger("Waiting for container creation...")
                    self.sleeper(wait_time_between_attempts)
                    continue
                elif state.waiting.reason in [
                    KubernetesWaitingReasons.ErrImagePull,
                    KubernetesWaitingReasons.ImagePullBackOff,
                    KubernetesWaitingReasons.CrashLoopBackOff,
                    KubernetesWaitingReasons.RunContainerError,
                ]:
                    raise DagsterK8sError(
                        'Failed: Reason="{reason}" Message="{message}"'.format(
                            reason=state.waiting.reason, message=state.waiting.message
                        )
                    )
                else:
                    raise DagsterK8sError("Unknown issue: %s" % state.waiting)

            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstateterminated-v1-core
            elif state.terminated is not None:
                if not state.terminated.exit_code == 0:
                    raw_logs = self.retrieve_pod_logs(pod_name, namespace)
                    message = state.terminated.message
                    raise DagsterK8sError(
                        f'Pod did not exit successfully. Failed with message: "{message}" '
                        f'and pod logs: "{raw_logs}"'
                    )
                else:
                    self.logger("Pod {pod_name} exitted successfully".format(pod_name=pod_name))
                break

            else:
                raise DagsterK8sError("Should not get here, unknown pod state")

    def retrieve_pod_logs(self, pod_name: str, namespace: str) -> str:
        """Retrieves the raw pod logs for the pod named `pod_name` from Kubernetes.

        Args:
            pod_name (str): The name of the pod from which to retrieve logs.
            namespace (str): The namespace of the pod.

        Returns:
            str: The raw logs retrieved from the pod.
        """
        check.str_param(pod_name, "pod_name")
        check.str_param(namespace, "namespace")

        # We set _preload_content to False here to prevent the k8 python api from processing the response.
        # If the logs happen to be JSON - it will parse in to a dict and then coerce back to a str leaving
        # us with invalid JSON as the quotes have been switched to '
        #
        # https://github.com/kubernetes-client/python/issues/811
        return self.core_api.read_namespaced_pod_log(
            name=pod_name, namespace=namespace, _preload_content=False
        ).data.decode("utf-8")
