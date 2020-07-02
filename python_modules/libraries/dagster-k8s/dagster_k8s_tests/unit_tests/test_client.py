from dagster_k8s.client import DagsterKubernetesClient
from kubernetes.client.models import V1Job, V1JobList, V1JobStatus, V1ObjectMeta

from dagster.seven import mock


def test_wait_for_job_success():
    batch_api_mock = mock.MagicMock()
    logger_mock = mock.MagicMock()
    sleeper_mock = mock.MagicMock()

    job_name = 'a_job'
    namespace = 'a_namespace'

    a_job_metadata = V1ObjectMeta(name=job_name)

    a_job_is_launched_list = V1JobList(items=[V1Job(metadata=a_job_metadata)])
    batch_api_mock.list_namespaced_job.side_effect = [a_job_is_launched_list]

    completed_job = V1Job(metadata=a_job_metadata, status=V1JobStatus(failed=0, succeeded=1))
    batch_api_mock.read_namespaced_job_status.side_effect = [completed_job]

    client = DagsterKubernetesClient(
        batch_api=batch_api_mock,
        core_api=mock.MagicMock(),
        logger=logger_mock,
        sleeper=sleeper_mock,
    )

    client.wait_for_job_success(job_name, namespace)

    # logger should not have been called
    assert not logger_mock.mock_calls
    # sleeper should not have been called
    assert not sleeper_mock.mock_calls
