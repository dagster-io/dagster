from dagster import (
    DagsterInstance,
    DagsterRun,
    DagsterRunStatus,
    _check as check,
)
from dagster._core.launcher import WorkerStatus
from dagster._core.workspace.workspace import IWorkspace
from google.cloud.run_v2 import CancelExecutionRequest, GetExecutionRequest, RunJobRequest


def test_launch_run(
    instance: DagsterInstance, run: DagsterRun, workspace: IWorkspace, mock_jobs_client
):
    instance.launch_run(run.run_id, workspace)
    run = check.not_none(instance.get_run_by_id(run.run_id))

    # Assert the correct tag is set
    assert run.tags["cloud_run_job_execution_id"] == "test_execution_id"

    # Check that mock was called with correct args
    mock_jobs_client.run_job.assert_called_once()
    args, _ = mock_jobs_client.run_job.call_args
    assert isinstance(args[0], RunJobRequest)
    assert args[0].name == "projects/test_project/locations/test_region/jobs/test_job_name"


def test_terminate(
    instance: DagsterInstance,
    run: DagsterRun,
    workspace: IWorkspace,
    mock_jobs_client,
    mock_executions_client,
):
    instance.launch_run(run.run_id, workspace)
    assert instance.run_launcher.terminate(run.run_id)

    # Check that a cancellation engine event was emitted
    run = check.not_none(instance.get_run_by_id(run.run_id))
    assert run.status == DagsterRunStatus.CANCELED

    # Check that the execution client was called with the correct args
    assert mock_executions_client.cancel_execution.call_count == 1
    _, kwargs = mock_executions_client.cancel_execution.call_args
    request = kwargs["request"]
    assert isinstance(request, CancelExecutionRequest)
    assert (
        request.name
        == "projects/test_project/locations/test_region/jobs/test_job_name/executions/test_execution_id"
    )


def test_check_run_worker_health(
    instance: DagsterInstance,
    run: DagsterRun,
    workspace: IWorkspace,
    mock_jobs_client,
    mock_executions_client,
):
    instance.launch_run(run.run_id, workspace)
    run = check.not_none(instance.get_run_by_id(run.run_id))
    result = instance.run_launcher.check_run_worker_health(run)
    assert result.status == WorkerStatus.RUNNING
    assert mock_executions_client.get_execution.call_count == 1
    _, kwargs = mock_executions_client.get_execution.call_args
    request = kwargs["request"]
    assert isinstance(request, GetExecutionRequest)
    assert (
        request.name
        == "projects/test_project/locations/test_region/jobs/test_job_name/executions/test_execution_id"
    )

    instance.run_launcher.terminate(run.run_id)
    result = instance.run_launcher.check_run_worker_health(run)
    assert result.status == WorkerStatus.FAILED
    assert mock_executions_client.get_execution.call_count == 2
    _, kwargs = mock_executions_client.get_execution.call_args
    request = kwargs["request"]
    assert isinstance(request, GetExecutionRequest)
    assert (
        request.name
        == "projects/test_project/locations/test_region/jobs/test_job_name/executions/test_execution_id"
    )
