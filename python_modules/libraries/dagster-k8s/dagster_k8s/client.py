import logging
import time
from enum import Enum

import kubernetes
import six

from dagster import DagsterInstance, check
from dagster.core.storage.pipeline_run import PipelineRunStatus

DEFAULT_WAIT_TIMEOUT = 86400.0  # 1 day
DEFAULT_WAIT_BETWEEN_ATTEMPTS = 10.0  # 10 seconds
DEFAULT_JOB_POD_COUNT = 1  # expect job:pod to be 1:1 by default


class WaitForPodState(Enum):
    Ready = "READY"
    Terminated = "TERMINATED"


class DagsterK8sError(Exception):
    pass


class DagsterK8sPipelineStatusException(Exception):
    pass


class KubernetesWaitingReasons:
    PodInitializing = "PodInitializing"
    ContainerCreating = "ContainerCreating"
    ErrImagePull = "ErrImagePull"
    ImagePullBackOff = "ImagePullBackOff"
    CrashLoopBackOff = "CrashLoopBackOff"
    RunContainerError = "RunContainerError"


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

    def delete_job(
        self, job_name, namespace,
    ):
        """Delete Kubernetes Job. We also need to delete corresponding pods due to:
        https://github.com/kubernetes-client/python/issues/234

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")

        pod_names = self.get_pod_names_for_job(job_name, namespace)

        try:
            # Collect all the errors so that we can post-process before raising
            errors = []
            try:
                self.batch_api.delete_namespaced_job(name=job_name, namespace=namespace)
            except Exception as e:  # pylint: disable=broad-except
                errors.append(e)

            for pod_name in pod_names:
                try:
                    self.core_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
                except Exception as e:  # pylint: disable=broad-except
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

    def get_pod_names_for_job(self, job_name, namespace):
        """Get pod names that corresponds to job name

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
        """
        check.str_param(job_name, "job_name")
        check.str_param(namespace, "namespace")

        pods = self.core_api.list_namespaced_pod(
            label_selector="job-name=={}".format(job_name), namespace=namespace
        )

        pod_names = []
        for item in pods.items:
            pod_names.append(item.metadata.name)

        return pod_names

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
                Defaults to DEFAULT_WAIT_TIMEOUT.
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

        job = None
        start = self.timer()

        # Ensure we found the job that we launched
        while not job:
            if self.timer() - start > wait_timeout:

                raise DagsterK8sError("Timed out while waiting for job to launch")

            jobs = self.batch_api.list_namespaced_job(namespace=namespace)
            job = next((j for j in jobs.items if j.metadata.name == job_name), None)

            if not job:
                self.logger('Job "{job_name}" not yet launched, waiting'.format(job_name=job_name))
                self.sleeper(wait_time_between_attempts)

        # Wait for job completed status
        while True:
            if self.timer() - start > wait_timeout:
                raise DagsterK8sError("Timed out while waiting for job to complete")

            # See: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.11/#jobstatus-v1-batch
            status = self.batch_api.read_namespaced_job_status(job_name, namespace=namespace).status

            if status.failed and status.failed > 0:
                pods = self.core_api.list_namespaced_pod(
                    label_selector="job-name=={}".format(job_name), namespace=namespace
                )
                logs = {}
                for pod in pods.items:
                    pod_name = pod.metadata.name
                    try:
                        logs[pod_name] = self.core_api.read_namespaced_pod_log(
                            name=pod_name, namespace=namespace
                        )
                    except kubernetes.client.rest.ApiException as e:
                        logs[pod_name] = e

                raise DagsterK8sError(
                    "Encountered failed job pods with status: {}, and logs: {}".format(status, logs)
                )

            # done waiting for pod completion
            if status.succeeded == num_pods_to_wait_for:
                break

            if instance and run_id:
                pipeline_run_status = instance.get_run_by_id(run_id).status
                if pipeline_run_status != PipelineRunStatus.STARTED:
                    raise DagsterK8sPipelineStatusException()

            self.sleeper(wait_time_between_attempts)

    def retrieve_pod_logs(self, pod_name, namespace):
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
        return six.ensure_str(
            self.core_api.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, _preload_content=False
            ).data
        )

    def wait_for_job(
        self,
        job_name,
        namespace,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    ):
        """ Wait for a job to launch and be running.

        Args:
            job_name (str): Name of the job to wait for.
            namespace (str): Namespace in which the job is located.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT.
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

        start = self.timer()
        # Ensure we found the job that we launched
        while not job:
            if self.timer() - start > wait_timeout:
                raise DagsterK8sError("Timed out while waiting for job to launch")

            jobs = self.batch_api.list_namespaced_job(namespace=namespace)
            job = next((j for j in jobs.items if j.metadata.name == job_name), None)

            if not job:
                self.logger('Job "{job_name}" not yet launched, waiting'.format(job_name=job_name))
                self.sleeper(wait_time_between_attempts)

    def wait_for_pod(
        self,
        pod_name,
        namespace,
        wait_for_state=WaitForPodState.Ready,
        wait_timeout=DEFAULT_WAIT_TIMEOUT,
        wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    ):
        """Wait for a pod to launch and be running, or wait for termination (useful for job pods).

        Args:
            pod_name (str): Name of the pod to wait for.
            namespace (str): Namespace in which the pod is located.
            wait_for_state (WaitForPodState, optional): Whether to wait for pod readiness or
                termination. Defaults to waiting for readiness.
            wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
                Defaults to DEFAULT_WAIT_TIMEOUT.
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

        start = self.timer()

        while True:

            pods = self.core_api.list_namespaced_pod(
                namespace=namespace, field_selector="metadata.name=%s" % pod_name
            ).items
            pod = pods[0] if pods else None

            if self.timer() - start > wait_timeout:
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
                    raise DagsterK8sError(
                        'Pod did not exit successfully. Failed with message: "%s" and pod logs: "%s"'
                        % (state.terminated.message, str(raw_logs))
                    )
                else:
                    self.logger("Pod {pod_name} exitted successfully".format(pod_name=pod_name))
                break

            else:
                raise DagsterK8sError("Should not get here, unknown pod state")

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

        pods = self.core_api.list_namespaced_pod(
            namespace=namespace, label_selector="job-name={}".format(job_name)
        ).items
        return [p.metadata.name for p in pods]
