import time
from collections import namedtuple
from unittest import mock

import kubernetes
import pytest
from dagster_k8s.client import (
    DagsterK8sAPIRetryLimitExceeded,
    DagsterK8sError,
    DagsterK8sUnrecoverableAPIError,
    DagsterKubernetesClient,
    KubernetesWaitingReasons,
    WaitForPodState,
)
from kubernetes.client.models import (
    V1ContainerState,
    V1ContainerStateRunning,
    V1ContainerStateTerminated,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1Job,
    V1JobList,
    V1JobStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1PodStatus,
)


def create_mocked_client(batch_api=None, core_api=None, logger=None, sleeper=None, timer=None):
    return DagsterKubernetesClient(
        batch_api=batch_api or mock.MagicMock(),
        core_api=core_api or mock.MagicMock(),
        logger=logger or mock.MagicMock(),
        sleeper=sleeper or mock.MagicMock(),
        timer=timer or time.time,
    )


TIMEOUT_GAP = 1000000000000


# returns a fixed start time
# then N (num_good_ticks) each the previous value + 1
# then a very large number to simulate a timeout
def create_timing_out_timer(num_good_ticks):
    mock_timer = mock.MagicMock()
    times = [1593697070.443257]  # fixed time on 7/2/2020
    i = 0
    while i < num_good_ticks:
        times.append(times[-1] + 1)
        i += 1
    times.append(times[-1] + TIMEOUT_GAP)
    mock_timer.side_effect = times
    return mock_timer


def assert_logger_calls(mock_logger, log_messages):
    assert len(mock_logger.mock_calls) == len(log_messages)
    for mock_call, log_message in zip(mock_logger.mock_calls, log_messages):
        _name, args, _kwargs = mock_call
        assert args[0] == log_message


#####
# wait_for_job tests
#####


def test_wait_for_job_success():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [completed_job]

    mock_client.wait_for_job_success(job_name, namespace)

    # logger should not have been called
    assert not mock_client.logger.mock_calls
    # sleeper should not have been called
    assert not mock_client.sleeper.mock_calls


def test_create_job_success():
    mock_client = create_mocked_client()
    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    # Finishes without issue
    mock_client.create_namespaced_job_with_retries(
        body=V1Job(metadata=a_job_metadata),
        namespace=namespace,
    )


def test_create_job_failure_errors():
    mock_client = create_mocked_client()
    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    mock_client.batch_api.create_namespaced_job.side_effect = [
        kubernetes.client.rest.ApiException(status=500, reason="Bad"),
        kubernetes.client.rest.ApiException(status=500, reason="Worse"),
        kubernetes.client.rest.ApiException(status=500, reason="Even worse"),
        kubernetes.client.rest.ApiException(status=500, reason="The worst"),
    ]

    with pytest.raises(DagsterK8sAPIRetryLimitExceeded):
        mock_client.create_namespaced_job_with_retries(
            body=V1Job(metadata=a_job_metadata),
            namespace=namespace,
            wait_time_between_attempts=0,
        )


def test_create_job_with_idempotence_api_errors():
    mock_client = create_mocked_client()
    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    mock_client.batch_api.create_namespaced_job.side_effect = [
        kubernetes.client.rest.ApiException(
            status=500, reason="This is a lie, I actually made the job"
        ),
        kubernetes.client.rest.ApiException(status=409, reason="Job already exists"),
    ]

    mock_client.create_namespaced_job_with_retries(
        body=V1Job(metadata=a_job_metadata),
        namespace=namespace,
        wait_time_between_attempts=0,
    )


def test_wait_for_job_success_with_api_errors():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [
        kubernetes.client.rest.ApiException(status=503, reason="Service unavailable"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        completed_job,
    ]

    mock_client.wait_for_job_success(job_name, namespace, wait_time_between_attempts=0)

    # logger should not have been called
    assert not mock_client.logger.mock_calls
    # sleeper should not have been called
    assert not mock_client.sleeper.mock_calls

    # 2 attempts with errors + 1 SUCCESS
    assert len(mock_client.batch_api.read_namespaced_job_status.mock_calls) == 3


def test_wait_for_job_success_with_api_errors_retry_limit_exceeded():
    mock_client = create_mocked_client()

    job_name = "a_job"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [
        kubernetes.client.rest.ApiException(status=500, reason="Internal server error"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=503, reason="Service unavailable"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        completed_job,
    ]

    with pytest.raises(DagsterK8sAPIRetryLimitExceeded):
        mock_client.wait_for_job_success(
            "a_job",
            "a_namespace",
            wait_time_between_attempts=0,
        )

    # logger should not have been called
    assert not mock_client.logger.mock_calls
    # sleeper should not have been called
    assert not mock_client.sleeper.mock_calls

    # 4 attempts with errors
    assert len(mock_client.batch_api.read_namespaced_job_status.mock_calls) == 4


def test_wait_for_job_success_with_unrecoverable_api_errors():
    mock_client = create_mocked_client()

    job_name = "a_job"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    mock_client.batch_api.read_namespaced_job_status.side_effect = [
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=429, reason="Too many requests"),
    ]

    with pytest.raises(DagsterK8sUnrecoverableAPIError) as exc_info:
        mock_client.wait_for_job_success("a_job", "a_namespace", wait_time_between_attempts=0)

    assert "Unexpected error encountered in Kubernetes API Client." in str(exc_info.value)

    # logger should not have been called
    assert not mock_client.logger.mock_calls
    # sleeper should not have been called
    assert not mock_client.sleeper.mock_calls

    # 1 retry error 1 unrecoverable error
    assert len(mock_client.batch_api.read_namespaced_job_status.mock_calls) == 2


def test_wait_for_job_not_launched():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    not_launched_yet_list = V1JobList(items=[])
    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [
        not_launched_yet_list,
        a_job_is_launched_list,
    ]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [completed_job]

    mock_client.wait_for_job_success(job_name, namespace)

    assert_logger_calls(mock_client.logger, ['Job "a_job" not yet launched, waiting'])

    assert len(mock_client.sleeper.mock_calls) == 1


def test_timed_out_while_waiting_for_launch():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=0))

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success("a_job", "a_namespace")

    assert str(exc_info.value) == "Timed out while waiting for job a_job to launch"


def test_wait_for_job_with_api_errors():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    not_launched_yet_list = V1JobList(items=[])
    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        not_launched_yet_list,
        a_job_is_launched_list,
    ]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [completed_job]

    mock_client.wait_for_job_success(job_name, namespace, wait_time_between_attempts=0)

    # 2 attempts with errors + 1 not launched + 1 launched
    assert len(mock_client.batch_api.list_namespaced_job.mock_calls) == 4


def test_wait_for_job_with_api_errors_retry_limit_exceeded():
    mock_client = create_mocked_client()

    job_name = "a_job"

    a_job_metadata = V1ObjectMeta(name=job_name)

    not_launched_yet_list = V1JobList(items=[])
    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        kubernetes.client.rest.ApiException(status=504, reason="Gateway Timeout"),
        not_launched_yet_list,
        a_job_is_launched_list,
    ]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [completed_job]

    with pytest.raises(DagsterK8sAPIRetryLimitExceeded):
        mock_client.wait_for_job_success("a_job", "a_namespace", wait_time_between_attempts=0)

    # 4 attempts with errors
    assert len(mock_client.batch_api.list_namespaced_job.mock_calls) == 4


def test_timed_out_while_waiting_for_job_to_complete():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=1))

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success(job_name, namespace)

    assert str(exc_info.value) == "Timed out while waiting for job a_job to complete"


def test_job_failed():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    # failed job
    failed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=1, succeeded=0))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [failed_job]

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success(job_name, namespace)

    assert "Encountered failed job pods for job a_job with status" in str(exc_info.value)


def test_long_running_job():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    # running job
    running_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=0))
    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))

    mock_client.batch_api.read_namespaced_job_status.side_effect = [running_job, completed_job]

    mock_client.wait_for_job_success(job_name, namespace)

    # slept once waiting for job to complete
    assert len(mock_client.sleeper.mock_calls) == 1


def test_job_succeded_after_failure():
    mock_client = create_mocked_client()

    job_name = "a_job"
    namespace = "a_namespace"

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    # failed job
    failed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(active=1, failed=1, succeeded=0))
    completed_job = V1Job(
        metadata=a_job_metadata, status=V1JobStatus(active=0, failed=0, succeeded=1)
    )
    mock_client.batch_api.read_namespaced_job_status.side_effect = [failed_job, completed_job]

    mock_client.wait_for_job_success(job_name, namespace)

    assert len(mock_client.batch_api.read_namespaced_job_status.mock_calls) == 2


###
# retrieve_pod_logs
###


def test_retrieve_pod_logs():
    mock_client = create_mocked_client()

    MockResponse = namedtuple("MockResponse", "data")

    mock_client.core_api.read_namespaced_pod_log.side_effect = [MockResponse(b"a_string")]

    assert mock_client.retrieve_pod_logs("pod", "namespace") == "a_string"


def _pod_list_for_container_status(*container_statuses, init_container_statuses=None):
    return V1PodList(
        items=[
            V1Pod(
                status=V1PodStatus(
                    container_statuses=container_statuses,
                    init_container_statuses=init_container_statuses,
                )
            )
        ]
    )


def _ready_running_status(name="a_name"):
    return _create_status(
        state=V1ContainerState(running=V1ContainerStateRunning()), ready=True, name=name
    )


def _create_status(state, ready, name="a_name"):
    return V1ContainerStatus(
        image="an_image",
        image_id="an_image_id",
        name=name,
        restart_count=0,
        state=state,
        ready=ready,
    )


###
# wait_for_pod_success
###
def test_wait_for_pod_success():
    """Ready pod right away."""
    mock_client = create_mocked_client()

    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_ready_running_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"

    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [f'Waiting for pod "{pod_name}"', f'Pod "{pod_name}" is ready, done waiting'],
    )


def test_wait_for_launch_then_success():
    mock_client = create_mocked_client()

    no_pods = V1PodList(items=[])
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        no_pods,
        single_ready_running_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"

    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to launch...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )

    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_wait_for_statuses_then_success():
    mock_client = create_mocked_client()

    single_no_status_pod = V1PodList(items=[V1Pod(status=V1PodStatus())])
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())
    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_no_status_pod,
        single_ready_running_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"

    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            "Waiting for pod init_container or container status to be set by kubernetes...",
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )

    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_initial_timeout():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=0))
    not_ready_list = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=False)
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [not_ready_list, not_ready_list]

    pod_name = "a_pod"

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    # value of pod info is big blob of serialized dict info
    assert str(exc_info.value).startswith(
        "Timed out while waiting for pod to become ready with pod info:"
    )


def test_initial_timeout_with_no_pod():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=0))
    no_pods = V1PodList(items=[])

    mock_client.core_api.list_namespaced_pod.side_effect = [no_pods, no_pods]

    pod_name = "a_pod"

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    # a bit of a dubious state here but it works
    assert (
        str(exc_info.value) == "Timed out while waiting for pod to become ready with pod info: None"
    )


def test_running_but_not_ready():
    mock_client = create_mocked_client()

    single_not_ready_running_pod = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=False)
    )
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_not_ready_running_pod,
        single_not_ready_running_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"

    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to become ready...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_wait_for_ready_but_terminated():
    mock_client = create_mocked_client()

    ignored_container = _create_status(
        state=V1ContainerState(terminated=V1ContainerStateTerminated(exit_code=1)),
        ready=False,
        name="ignored",
    )
    single_pod_terminated_successful = _pod_list_for_container_status(
        ignored_container,
        _create_status(
            state=V1ContainerState(terminated=V1ContainerStateTerminated(exit_code=0)), ready=False
        ),
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_pod_terminated_successful,
        single_pod_terminated_successful,
    ]

    pod_name = "a_pod"
    container_name = "a_name"

    mock_client.wait_for_pod(
        pod_name=pod_name, namespace="namespace", ignore_containers={"ignored"}
    )

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f"Container {container_name} in {pod_name} has exited successfully",
            f"Pod {pod_name} exited successfully",
        ],
    )


def test_wait_for_ready_but_terminated_unsuccessfully():
    mock_client = create_mocked_client()

    single_not_ready_running_pod = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=False)
    )

    single_pod_terminated_unsuccessful = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(
                terminated=V1ContainerStateTerminated(exit_code=1, message="error_message")
            ),
            ready=False,
        )
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_not_ready_running_pod,
        single_pod_terminated_unsuccessful,
    ]

    retrieve_pod_logs_mock = mock.MagicMock()
    retrieve_pod_logs_mock.side_effect = ["raw_logs_ret_val"]
    mock_client.retrieve_pod_logs = retrieve_pod_logs_mock

    pod_name = "a_pod"
    container_name = "a_name"

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert (
        str(exc_info.value)
        == f'Pod {pod_name} terminated but some containers exited with errors:\nContainer "{container_name}" failed with message: "error_message" '
        'and pod logs: "raw_logs_ret_val"'
    )


def test_wait_for_termination_ready_then_terminate():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=3))

    single_not_ready_running_pod = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=False)
    )
    single_pod_terminated_successful = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(terminated=V1ContainerStateTerminated(exit_code=0)), ready=False
        )
    )
    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_not_ready_running_pod,
        single_not_ready_running_pod,
        single_pod_terminated_successful,
    ]

    pod_name = "a_pod"
    container_name = "a_name"

    mock_client.wait_for_pod(
        pod_name=pod_name, namespace="namespace", wait_for_state=WaitForPodState.Terminated
    )

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f"Container {container_name} in {pod_name} has exited successfully",
            f"Pod {pod_name} exited successfully",
        ],
    )

    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_waiting_for_pod_initialize():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=3))
    single_waiting_pod = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(
                waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
            ),
            ready=False,
        )
    )
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_waiting_pod,
        single_waiting_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_waiting_for_pod_initialize_with_ignored_containers():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=4))
    ignored_waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
        name="ignored",
    )
    ignored_ready = _ready_running_status(name="ignored")
    waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    ready = _ready_running_status()

    mock_client.core_api.list_namespaced_pod.side_effect = [
        _pod_list_for_container_status(
            ignored_waiting_container_status,
            waiting_container_status,
        ),
        _pod_list_for_container_status(
            ignored_waiting_container_status,
            waiting_container_status,
        ),
        _pod_list_for_container_status(
            ignored_ready,
            waiting_container_status,
        ),
        _pod_list_for_container_status(
            ignored_ready,
            ready,
        ),
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(
        pod_name=pod_name, namespace="namespace", ignore_containers={"ignored"}
    )

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 2


def test_waiting_for_pod_initialize_with_init_container():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=3))
    waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    single_waiting_pod = _pod_list_for_container_status(
        waiting_container_status, init_container_statuses=[waiting_container_status]
    )
    single_ready_running_pod = _pod_list_for_container_status(
        waiting_container_status, init_container_statuses=[_ready_running_status()]
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_waiting_pod,
        single_waiting_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_wait_for_pod_initialize_with_multiple_init_containers():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=4))
    waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    waiting_initcontainer1_status = _create_status(
        name="init1",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    waiting_initcontainer2_status = _create_status(
        name="init2",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    ready_initcontainer1_status = _ready_running_status(name="init1")
    ready_initcontainer2_status = _ready_running_status(name="init2")

    two_waiting_inits_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[waiting_initcontainer1_status, waiting_initcontainer2_status],
    )
    single_init_ready_waiting_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[ready_initcontainer1_status, waiting_initcontainer2_status],
    )
    both_init_ready_waiting_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[ready_initcontainer1_status, ready_initcontainer2_status],
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [
        two_waiting_inits_pod,
        two_waiting_inits_pod,
        single_init_ready_waiting_pod,
        both_init_ready_waiting_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )


# Container states are evaluated in the order that they are in the pod manifest, but
# it's possible that the second initcontainer can finish first and we test that here.
def test_wait_for_pod_initialize_with_multiple_init_containers_backwards():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=5))
    waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    waiting_initcontainer1_status = _create_status(
        name="init1",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    waiting_initcontainer2_status = _create_status(
        name="init2",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    ready_initcontainer1_status = _ready_running_status(name="init1")
    ready_initcontainer2_status = _ready_running_status(name="init2")

    two_waiting_inits_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[waiting_initcontainer1_status, waiting_initcontainer2_status],
    )
    single_init_ready_waiting_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[waiting_initcontainer1_status, ready_initcontainer2_status],
    )
    both_init_ready_waiting_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[ready_initcontainer1_status, ready_initcontainer2_status],
    )

    # we need an extra side effect here compared to the above test since
    # there's an extra loop iteration
    mock_client.core_api.list_namespaced_pod.side_effect = [
        two_waiting_inits_pod,
        two_waiting_inits_pod,
        single_init_ready_waiting_pod,
        both_init_ready_waiting_pod,
        both_init_ready_waiting_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Waiting for pod "{pod_name}" to initialize...',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )


# init containers may terminate quickly, so a ready state is never observed
def test_wait_for_pod_initialize_with_fast_init_containers():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=5))
    waiting_container_status = _create_status(
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
        name="main",
    )
    waiting_initcontainer_slow_status = _create_status(
        name="init_slow",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    waiting_initcontainer_fast_status = _create_status(
        name="init_fast",
        state=V1ContainerState(
            waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.PodInitializing)
        ),
        ready=False,
    )
    terminated_initcontainer_fast_status = _create_status(
        name="init_fast",
        ready=False,
        state=V1ContainerState(terminated=V1ContainerStateTerminated(exit_code=0)),
    )
    ready_initcontainer_slow_status = _ready_running_status(name="init_slow")

    two_waiting_inits_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[
            waiting_initcontainer_slow_status,
            waiting_initcontainer_fast_status,
        ],
    )
    term_and_ready_waiting_pod = _pod_list_for_container_status(
        waiting_container_status,
        init_container_statuses=[
            terminated_initcontainer_fast_status,
            ready_initcontainer_slow_status,
        ],
    )

    mock_client.core_api.list_namespaced_pod.side_effect = [
        two_waiting_inits_pod,
        two_waiting_inits_pod,
        term_and_ready_waiting_pod,
        term_and_ready_waiting_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Waiting for pod "{pod_name}" to initialize...',
            "Init container init_fast in a_pod has exited successfully",
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )


def test_waiting_for_pod_container_creation():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=3))
    single_waiting_pod = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(
                waiting=V1ContainerStateWaiting(reason=KubernetesWaitingReasons.ContainerCreating)
            ),
            ready=False,
        )
    )
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_waiting_pod,
        single_waiting_pod,
        single_ready_running_pod,
    ]

    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            "Waiting for container creation...",
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    # slept only once
    assert len(mock_client.sleeper.mock_calls) == 1


def test_valid_failure_waiting_reasons():
    mock_client = create_mocked_client()
    for reason in [
        KubernetesWaitingReasons.ErrImagePull,
        KubernetesWaitingReasons.ImagePullBackOff,
        KubernetesWaitingReasons.CrashLoopBackOff,
        KubernetesWaitingReasons.RunContainerError,
    ]:
        single_waiting_pod_failure = _pod_list_for_container_status(
            _create_status(
                state=V1ContainerState(
                    waiting=V1ContainerStateWaiting(reason=reason, message="bad things")
                ),
                ready=False,
            )
        )
        mock_client.core_api.list_namespaced_pod.side_effect = [
            single_waiting_pod_failure,
            single_waiting_pod_failure,
        ]
        pod_name = "a_pod"
        with pytest.raises(DagsterK8sError) as exc_info:
            mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")
        assert f'Failed: Reason="{reason}" Message="bad things"' in str(exc_info.value)


def test_waiting_reason_none():
    mock_client = create_mocked_client()
    single_waiting_pod = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(waiting=V1ContainerStateWaiting(reason=None, message=None)),
            ready=False,
        )
    )
    single_ready_running_pod = _pod_list_for_container_status(_ready_running_status())

    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_waiting_pod,
        single_waiting_pod,
        single_ready_running_pod,
    ]
    pod_name = "a_pod"
    mock_client.wait_for_pod(pod_name="a_pod", namespace="namespace")
    assert_logger_calls(
        mock_client.logger,
        [
            f'Waiting for pod "{pod_name}"',
            f'Pod "{pod_name}" is waiting with reason "None" - this is temporary/transition state',
            f'Pod "{pod_name}" is ready, done waiting',
        ],
    )
    assert len(mock_client.sleeper.mock_calls) == 1


def test_bad_waiting_state():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=2))
    single_waiting_pod = _pod_list_for_container_status(
        _create_status(
            state=V1ContainerState(waiting=V1ContainerStateWaiting(reason="InvalidReason")),
            ready=False,
        )
    )
    mock_client.core_api.list_namespaced_pod.side_effect = [single_waiting_pod, single_waiting_pod]
    pod_name = "a_pod"
    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert str(exc_info.value) == "Unknown issue: {'message': None, 'reason': 'InvalidReason'}"


def test_get_names_in_job():
    pod_list = V1PodList(
        items=[V1Pod(metadata=V1ObjectMeta(name="foo")), V1Pod(metadata=V1ObjectMeta(name="bar"))]
    )
    mock_client = create_mocked_client()

    mock_client.core_api.list_namespaced_pod.side_effect = [pod_list, pod_list]

    assert mock_client.get_pod_names_in_job("job", "namespace") == ["foo", "bar"]


def test_wait_for_termination_pod_is_deleted():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=2))

    single_ready_running_pod = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=True)
    )

    empty_pod_list = V1PodList(items=[])
    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_ready_running_pod,
        empty_pod_list,
    ]

    pod_name = "a_pod"

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(
            pod_name=pod_name, namespace="namespace", wait_for_state=WaitForPodState.Terminated
        )

    assert str(exc_info.value).startswith(f'Pod "{pod_name}" was unexpectedly killed')


def test_wait_for_ready_pod_is_deleted():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=2))

    single_not_ready_running_pod = _pod_list_for_container_status(
        _create_status(state=V1ContainerState(running=V1ContainerStateRunning()), ready=False)
    )

    empty_pod_list = V1PodList(items=[])
    mock_client.core_api.list_namespaced_pod.side_effect = [
        single_not_ready_running_pod,
        empty_pod_list,
    ]

    pod_name = "a_pod"

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_pod(pod_name=pod_name, namespace="namespace")

    assert str(exc_info.value).startswith(f'Pod "{pod_name}" was unexpectedly killed')
