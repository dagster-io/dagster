import time

import pytest
from dagster_k8s.client import DagsterK8sError, DagsterKubernetesClient
from kubernetes.client.models import V1Job, V1JobList, V1JobStatus, V1ObjectMeta

from dagster.seven import mock


def create_mocked_client(batch_api=None, core_api=None, logger=None, sleeper=None, timer=None):
    return DagsterKubernetesClient(
        batch_api=batch_api or mock.MagicMock(),
        core_api=core_api or mock.MagicMock(),
        logger=logger or mock.MagicMock(),
        sleeper=sleeper or mock.MagicMock(),
        timer=timer or time.time,
    )


def test_wait_for_job_success():
    mock_client = create_mocked_client()

    job_name = 'a_job'
    namespace = 'a_namespace'

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


def test_wait_for_job_not_launched():
    mock_client = create_mocked_client()

    job_name = 'a_job'
    namespace = 'a_namespace'

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

    assert len(mock_client.logger.mock_calls) == 1
    _name, args, _kwargs = mock_client.logger.mock_calls[0]
    assert args == ('Job "a_job" not yet launched, waiting',)

    assert len(mock_client.sleeper.mock_calls) == 1


def test_timed_out_while_waiting_for_launch():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=0))

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success('a_job', 'a_namespace')

    assert str(exc_info.value) == 'Timed out while waiting for job to launch'


def test_timed_out_while_waiting_for_job_to_complete():
    mock_client = create_mocked_client(timer=create_timing_out_timer(num_good_ticks=1))

    job_name = 'a_job'
    namespace = 'a_namespace'

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success(job_name, namespace)

    assert str(exc_info.value) == 'Timed out while waiting for job to complete'


def test_job_failed():
    mock_client = create_mocked_client()

    job_name = 'a_job'
    namespace = 'a_namespace'

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    mock_client.batch_api.list_namespaced_job.side_effect = [a_job_is_launched_list]

    # failed job
    failed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=1, succeeded=0))
    mock_client.batch_api.read_namespaced_job_status.side_effect = [failed_job]

    with pytest.raises(DagsterK8sError) as exc_info:
        mock_client.wait_for_job_success(job_name, namespace)

    assert 'Encountered failed job pods with status' in str(exc_info.value)


def test_long_running_job():
    mock_client = create_mocked_client()

    job_name = 'a_job'
    namespace = 'a_namespace'

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
