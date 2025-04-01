import logging
import sys
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

import kubernetes.client
import kubernetes.client.rest
import six
from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from kubernetes.client.api_client import ApiClient
from kubernetes.client.models import V1Job, V1JobStatus

try:
    from kubernetes.client.models import EventsV1Event  # noqa

    K8S_EVENTS_API_PRESENT = True
except ImportError:
    K8S_EVENTS_API_PRESENT = False


T = TypeVar("T")

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
        super().__init__(
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
        super().__init__(args[0], *args[1:], **kwargs)

        self.k8s_api_exception = check.opt_inst_param(
            k8s_api_exception, "k8s_api_exception", Exception
        )
        self.original_exc_info = original_exc_info


class DagsterK8sJobStatusException(Exception):
    pass


WHITELISTED_TRANSIENT_K8S_STATUS_CODES = [
    503,  # Service unavailable
    504,  # Gateway timeout
    500,  # Internal server error
    # typically not transient, but some k8s clusters raise it transiently: https://github.com/aws/containers-roadmap/issues/1810
    401,  # Authorization Failure
]


class PatchedApiClient(ApiClient):
    # Forked from ApiClient implementation to pass configuration object down into created model
    # objects, avoiding lock contention issues. See https://github.com/kubernetes-client/python/issues/2284
    # Intentionally circumventing private name mangling
    # (https://docs.python.org/3/reference/expressions.html#private-name-mangling) of the __deserialize_model method on ApiClient
    def _ApiClient__deserialize_model(self, data, klass):
        """Deserializes list or dict to model.

        :param data: dict, list.
        :param klass: class literal.
        :return: model object.
        """
        if not klass.openapi_types and not hasattr(klass, "get_real_child_model"):
            return data

        # Below is the only change from the base ApiClient implementation - pass through the
        # Configuration object to each newly created model so that each one does not have to create
        # one and acquire a lock
        kwargs = {"local_vars_configuration": self.configuration}

        if data is not None and klass.openapi_types is not None and isinstance(data, (list, dict)):
            for attr, attr_type in six.iteritems(klass.openapi_types):
                if klass.attribute_map[attr] in data:
                    value = data[klass.attribute_map[attr]]
                    kwargs[attr] = self._ApiClient__deserialize(value, attr_type)

        instance = klass(**kwargs)

        if hasattr(instance, "get_real_child_model"):
            klass_name = instance.get_real_child_model(data)
            if klass_name:
                instance = self._ApiClient__deserialize(data, klass_name)
        return instance


def k8s_api_retry(
    fn: Callable[..., T],
    max_retries: int,
    timeout: float,
    msg_fn=lambda: "Unexpected error encountered in Kubernetes API Client.",
) -> T:
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
    check.failed("Unreachable.")


def k8s_api_retry_creation_mutation(
    fn: Callable[..., None],
    max_retries: int,
    timeout: float,
    msg_fn=lambda: "Unexpected error encountered in Kubernetes API Client.",
) -> None:
    """Like k8s_api_retry, but ensures idempotence by allowing a 409 error after
    a failure, which indicates that the desired mutation actually went through.
    Also has an empty return type since we can't guarantee on being able to
    return anything as a result of this case.
    """
    check.callable_param(fn, "fn")
    check.int_param(max_retries, "max_retries")
    check.numeric_param(timeout, "timeout")

    remaining_attempts = 1 + max_retries
    retry_count = 0
    while remaining_attempts > 0:
        remaining_attempts -= 1

        try:
            fn()
            return
        except kubernetes.client.rest.ApiException as e:
            retry_count = retry_count + 1
            # Only catch whitelisted ApiExceptions
            status = e.status

            # 409 (Conflict) here indicates that hte object actually was created
            # during a previous attempt, despite logging a failure
            if retry_count > 1 and status == 409:
                return

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
    check.failed("Unreachable.")


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
    def production_client(batch_api_override=None, core_api_override=None):
        return DagsterKubernetesClient(
            batch_api=(
                batch_api_override or kubernetes.client.BatchV1Api(api_client=PatchedApiClient())
            ),
            core_api=(
                core_api_override or kubernetes.client.CoreV1Api(api_client=PatchedApiClient())
            ),
            logger=logging.info,
            sleeper=time.sleep,
            timer=time.time,
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
                    f"Timed out while waiting for job {job_name} to launch"
                )

            # Get all jobs in the namespace and find the matching job
            def _get_jobs_for_namespace():
                jobs = self.batch_api.list_namespaced_job(
                    namespace=namespace, field_selector=f"metadata.name={job_name}"
                )
                if jobs.items:
                    check.invariant(
                        len(jobs.items) == 1,
                        f'There should only be one k8s job with name "{job_name}", but got multiple'
                        f' jobs:" {jobs.items}',
                    )
                    return jobs.items[0]
                else:
                    return None

            job = k8s_api_retry(
                _get_jobs_for_namespace, max_retries=3, timeout=wait_time_between_attempts
            )

            if not job:
                self.logger(f'Job "{job_name}" not yet launched, waiting')
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
                    f"Timed out while waiting for job {job_name} to have pods"
                )

            pod_list = k8s_api_retry(_get_pods, max_retries=3, timeout=wait_time_between_attempts)

            if pod_list:
                return pod_list

            self.logger(f'Job "{job_name}" does not yet have pods, waiting')
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
                    f"Timed out while waiting for job {job_name} to complete"
                )

            # Reads the status of the specified job. Returns a V1Job object that
            # we need to read the status off of.
            status = self.get_job_status(
                job_name=job_name,
                namespace=namespace,
                wait_time_between_attempts=wait_time_between_attempts,
            )

            if not status:
                raise DagsterK8sError(f"job {job_name} could not be found")

            # status.succeeded represents the number of pods which reached phase Succeeded.
            if status.succeeded == num_pods_to_wait_for:
                break

            # status.failed represents the number of pods which reached phase Failed.
            # if there are any active runs do not raise an exception. This happens when the job
            # is created with a backoff_limit > 0.
            if (
                (status.active is None or status.active == 0)
                and status.failed
                and status.failed > 0
            ):
                raise DagsterK8sError(
                    f"Encountered failed job pods for job {job_name} with status: {status}, "
                    f"in namespace {namespace}"
                )

            if instance and run_id:
                dagster_run = instance.get_run_by_id(run_id)
                if not dagster_run:
                    raise DagsterK8sJobStatusException()

                dagster_run_status = dagster_run.status
                if dagster_run_status != DagsterRunStatus.STARTED:
                    raise DagsterK8sJobStatusException()

            self.sleeper(wait_time_between_attempts)

    def get_job_status(
        self,
        job_name: str,
        namespace: str,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    ) -> Optional[V1JobStatus]:
        def _get_job_status():
            try:
                job = self.batch_api.read_namespaced_job_status(job_name, namespace=namespace)
            except kubernetes.client.rest.ApiException as e:
                if e.status == 404:
                    return None
                else:
                    raise

            return job.status

        return k8s_api_retry(_get_job_status, max_retries=3, timeout=wait_time_between_attempts)

    def delete_job(
        self,
        job_name,
        namespace,
    ):
        """Delete Kubernetes Job.

        We also need to delete corresponding pods due to:

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
                        and error.status == 404
                    ):
                        raise error
                raise errors[0]

            return True
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
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
            namespace=namespace, label_selector=f"job-name={job_name}"
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
        pod_name: str,
        namespace: str,
        wait_for_state: WaitForPodState = WaitForPodState.Ready,
        pod_launch_timeout: float = DEFAULT_WAIT_TIMEOUT,
        wait_timeout: float = DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts: float = DEFAULT_WAIT_BETWEEN_ATTEMPTS,
        start_time: Any = None,
        ignore_containers: Optional[set] = None,
    ) -> None:
        """Wait for a pod to launch and be running, or wait for termination (useful for job pods).

        Args:
        ----
            pod_name (str): Name of the pod to wait for.
            namespace (str): Namespace in which the pod is located.
            wait_for_state (WaitForPodState, optional): Whether to wait for pod readiness or
                termination. Defaults to waiting for readiness.
            pod_launch_timeout (numeric, optional): Timeout after which to give up and raise exception
                if the pod never appears. Defaults to DEFAULT_WAIT_TIMEOUT. Set to 0 to disable.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT. Set to 0 to disable.
            wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
                to DEFAULT_WAIT_BETWEEN_ATTEMPTS.
            start_time (numeric, optional): The start time of the wait, used for testing.
            ignore_containers (set, optional): The container names that we should ignore
                when waiting for the pod to be ready/terminate.

        Raises:
        ------
            DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered

        """
        check.str_param(pod_name, "pod_name")
        check.str_param(namespace, "namespace")
        check.inst_param(wait_for_state, "wait_for_state", WaitForPodState)
        check.numeric_param(wait_timeout, "wait_timeout")
        check.numeric_param(pod_launch_timeout, "pod_launch_timeout")
        check.numeric_param(wait_time_between_attempts, "wait_time_between_attempts")

        self.logger(f'Waiting for pod "{pod_name}"')

        start = start_time or self.timer()

        # A set of container names that have exited.
        exited_containers = set()
        ready_containers = set()
        ignore_containers = ignore_containers or set()
        error_logs = []

        while True:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, field_selector=f"metadata.name={pod_name}"
            ).items
            pod = pods[0] if pods else None

            if pod_launch_timeout and self.timer() - start > pod_launch_timeout:
                raise DagsterK8sError(
                    f"Timed out while waiting for pod to become ready with pod info: {pod!s}"
                )

            if pod is None:
                self.logger(f'Waiting for pod "{pod_name}" to launch...')
                self.sleeper(wait_time_between_attempts)
                continue

            if not pod.status.init_container_statuses and not pod.status.container_statuses:
                self.logger(
                    "Waiting for pod init_container or container status to be set by kubernetes..."
                )
                self.sleeper(wait_time_between_attempts)
                continue
            break

        while True:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, field_selector=f"metadata.name={pod_name}"
            ).items
            pod = pods[0] if pods else None
            if pod is None:
                raise DagsterK8sError(f'Pod "{pod_name}" was unexpectedly killed')

            if wait_timeout and self.timer() - start > wait_timeout:
                raise DagsterK8sError(
                    f"Timed out while waiting for pod to get to status {wait_for_state.value} with pod info: {pod!s}"
                )
            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstatus-v1-core
            all_statuses = []
            all_statuses.extend(pod.status.init_container_statuses or [])
            all_statuses.extend(pod.status.container_statuses or [])
            initcontainers = set(s.name for s in (pod.status.init_container_statuses or []))

            # Filter out ignored containers
            all_statuses = [s for s in all_statuses if s.name not in ignore_containers]

            # Always get the first status from the list, which will first get the
            # init container (if it exists), then will iterate through the loop
            # of all containers if we are waiting for termination.
            #
            # In case we are waiting for the pod to be ready, we will exit after
            # the first container in this list is ready.
            container_status = next(
                s for s in all_statuses if s.name not in exited_containers | ready_containers
            )

            # State checks below, see:
            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstate-v1-core
            state = container_status.state
            if state.running is not None:
                if wait_for_state == WaitForPodState.Ready:
                    # ready is boolean field of container status
                    ready = container_status.ready
                    if not ready:
                        self.logger(f'Waiting for pod "{pod_name}" to become ready...')
                        self.sleeper(wait_time_between_attempts)
                        continue
                    else:
                        ready_containers.add(container_status.name)
                        if container_status.name in initcontainers:
                            self.logger(
                                f'Init container "{container_status.name}" is ready, waiting for non-init containers...'
                            )
                            continue
                        if initcontainers.issubset(exited_containers | ready_containers):
                            self.logger(f'Pod "{pod_name}" is ready, done waiting')
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
                    self.logger(f'Waiting for pod "{pod_name}" to initialize...')
                    self.sleeper(wait_time_between_attempts)
                    continue
                if state.waiting.reason == KubernetesWaitingReasons.CreateContainerConfigError:
                    self.logger(
                        f'Pod "{pod_name}" is waiting due to a CreateContainerConfigError with message "{state.waiting.message}"'
                        " - trying again to see if it recovers"
                    )
                    self.sleeper(wait_time_between_attempts)
                    continue
                elif state.waiting.reason == KubernetesWaitingReasons.ContainerCreating:
                    self.logger("Waiting for container creation...")
                    self.sleeper(wait_time_between_attempts)
                    continue
                elif state.waiting.reason is None:
                    self.logger(
                        f'Pod "{pod_name}" is waiting with reason "None" - this is temporary/transition state'
                    )
                    self.sleeper(wait_time_between_attempts)
                    continue
                elif state.waiting.reason in [
                    KubernetesWaitingReasons.ErrImagePull,
                    KubernetesWaitingReasons.ImagePullBackOff,
                    KubernetesWaitingReasons.CrashLoopBackOff,
                    KubernetesWaitingReasons.RunContainerError,
                ]:
                    debug_info = self.get_pod_debug_info(pod_name, namespace, pod=pod)
                    raise DagsterK8sError(
                        f'Failed: Reason="{state.waiting.reason}"'
                        f' Message="{state.waiting.message}"\n{debug_info}'
                    )
                else:
                    raise DagsterK8sError(f"Unknown issue: {state.waiting}")

            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstateterminated-v1-core
            elif state.terminated is not None:
                container_name = container_status.name
                if state.terminated.exit_code != 0:
                    raw_logs = self.retrieve_pod_logs(
                        pod_name, namespace, container_name=container_name
                    )
                    message = state.terminated.message
                    msg = (
                        f'Container "{container_name}" failed with message: "{message}" '
                        f'and pod logs: "{raw_logs}"'
                    )

                    self.logger(msg)
                    error_logs.append(msg)
                elif container_name in initcontainers:
                    self.logger(
                        f"Init container {container_name} in {pod_name} has exited successfully"
                    )
                else:
                    self.logger(f"Container {container_name} in {pod_name} has exited successfully")

                exited_containers.add(container_name)
                if len(all_statuses) != len(exited_containers):
                    continue

                if error_logs:
                    logs = "\n\n".join(error_logs)
                    raise DagsterK8sError(
                        f"Pod {pod_name} terminated but some containers exited with errors:\n{logs}"
                    )
                else:
                    self.logger(f"Pod {pod_name} exited successfully")
                break

            else:
                raise DagsterK8sError("Should not get here, unknown pod state")

    def retrieve_pod_logs(
        self,
        pod_name: str,
        namespace: str,
        container_name: Optional[str] = None,
        **kwargs,
    ) -> str:
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
            name=pod_name,
            namespace=namespace,
            container=container_name,
            _preload_content=False,
            **kwargs,
        ).data.decode("utf-8")

    def _get_container_status_str(self, container_status):
        state = container_status.state
        # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ContainerState.md
        if state.running:
            return "Ready" if container_status.ready else "Running but not ready"
        elif state.terminated:
            return f"Terminated with exit code {state.terminated.exit_code}: " + (
                f"{state.terminated.reason}: {state.terminated.message}"
                if state.terminated.message
                else f"{state.terminated.reason}"
            )
        elif state.waiting:
            return (
                f"Waiting: {state.waiting.reason}: {state.waiting.message}"
                if state.waiting.message
                else f"Waiting: {state.waiting.reason}"
            )

    def _get_pod_status_str(self, pod):
        if not pod.status:
            return "Could not determine pod status."

        pod_status = [
            f"Pod status: {pod.status.phase}"
            + (f": {pod.status.message}" if pod.status.message else "")
        ]

        if pod.status.container_statuses:
            pod_status.extend(
                [
                    f"Container '{status.name}' status: {self._get_container_status_str(status)}"
                    for status in pod.status.container_statuses
                ]
            )
        return "\n".join(pod_status)

    def retrieve_pod_events(
        self,
        pod_name: str,
        namespace: str,
    ) -> list[Any]:
        # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/EventsV1Event.md
        field_selector = f"involvedObject.name={pod_name}"
        return self.core_api.list_namespaced_event(namespace, field_selector=field_selector).items

    def _has_container_logs(self, container_status):
        # Logs are availalbe if either the container is running or terminated, or it's waiting
        # but previously ran or terminated
        if container_status.state:
            if container_status.state.running or container_status.state.terminated:
                return True

        if container_status.last_state:
            if container_status.last_state.running or container_status.last_state.terminated:
                return True

        return False

    def _get_job_status_str(self, job):
        if not job.status:
            return "Could not determine job status."

        job_status = (
            "Job status:"
            + f"\n - start_time: {job.status.start_time.isoformat()}"
            + f"\n - active={job.status.active or 'None'}"
            + f"\n - succeeded={job.status.succeeded or 'None'}"
            + f"\n - failed={job.status.failed or 'None'}"
        )

        return job_status

    def get_job_debug_info(
        self,
        job_name: str,
        namespace: str,
    ) -> str:
        jobs = self.batch_api.list_namespaced_job(
            namespace=namespace, field_selector=f"metadata.name={job_name}"
        ).items
        job = jobs[0] if jobs else None

        job_status_str = self._get_job_status_str(job) if job else f"Could not find job {job_name}"

        event_strs = []

        if job:
            events = self.core_api.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={job_name}",
            ).items
            for event in events:
                event_strs.append(f"{event.reason}: {event.message}")

        return (
            f"Debug information for job {job_name}:"
            + f"\n\n{job_status_str}"
            + "".join(["\n\n" + event_str for event_str in event_strs])
        )

    def get_pod_debug_info(
        self,
        pod_name,
        namespace,
        pod: Optional[kubernetes.client.V1Pod] = None,  # the already fetched pod
        include_container_logs: Optional[bool] = True,
    ) -> str:
        if pod is None:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, field_selector=f"metadata.name={pod_name}"
            ).items
            pod = pods[0] if pods else None

        pod_status_str = self._get_pod_status_str(pod) if pod else f"Could not find pod {pod_name}"

        log_strs = []

        specific_warnings = []

        container_statuses_by_name = (
            {status.name: status for status in pod.status.container_statuses}
            if pod and pod.status and pod.status.container_statuses
            else {}
        )

        if include_container_logs:
            for container in (
                pod.spec.containers if (pod and pod.spec and pod.spec.containers) else []
            ):
                container_name = container.name
                log_str = ""

                container_status = container_statuses_by_name.get(container_name)

                if not container_status or not self._has_container_logs(container_status):
                    log_str = f"No logs for container '{container_name}'."
                else:
                    try:
                        pod_logs = self.retrieve_pod_logs(
                            pod_name,
                            namespace,
                            container_name,
                            tail_lines=25,
                            timestamps=True,
                        )
                        # Remove trailing newline if present
                        pod_logs = pod_logs[:-1] if pod_logs.endswith("\n") else pod_logs

                        if "exec format error" in pod_logs:
                            specific_warnings.append(
                                f"Logs for container '{container_name}' contained `exec format error`, which usually means that your"
                                " Docker image was built using the wrong architecture.\nTry rebuilding your"
                                " docker image with the `--platform linux/amd64` flag set."
                            )
                        log_str = (
                            f"Last 25 log lines for container '{container_name}':\n{pod_logs}"
                            if pod_logs
                            else f"No logs for container '{container_name}'."
                        )

                    except kubernetes.client.rest.ApiException as e:
                        log_str = f"Failure fetching pod logs for container '{container_name}': {e}"

                log_strs.append(log_str)

        if not K8S_EVENTS_API_PRESENT:
            warning_str = (
                "Could not fetch pod events: the k8s events API is not available in the current"
                " version of the Python kubernetes client."
            )
        else:
            try:
                pod_events = self.retrieve_pod_events(pod_name, namespace)
                warning_events = [event for event in pod_events if event.type == "Warning"]

                if not warning_events:
                    warning_str = "No warning events for pod."
                else:
                    event_strs = []
                    for event in warning_events:
                        count_str = (
                            f" (x{event.count})" if (event.count and event.count > 1) else ""
                        )
                        event_strs.append(f"{event.reason}: {event.message}{count_str}")
                    warning_str = "Warning events for pod:\n" + "\n".join(event_strs)

            except kubernetes.client.rest.ApiException as e:
                warning_str = f"Failure fetching pod events: {e}"

        return (
            f"Debug information for pod {pod_name}:"
            + f"\n\n{pod_status_str}"
            + "".join(["\n\n" + specific_warning for specific_warning in specific_warnings])
            + "".join(["\n\n" + log_str for log_str in log_strs])
            + f"\n\n{warning_str}"
        )

    def create_namespaced_job_with_retries(
        self,
        body: V1Job,
        namespace: str,
        wait_time_between_attempts: float = DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    ) -> None:
        k8s_api_retry_creation_mutation(
            lambda: self.batch_api.create_namespaced_job(body=body, namespace=namespace),
            max_retries=3,
            timeout=wait_time_between_attempts,
        )
