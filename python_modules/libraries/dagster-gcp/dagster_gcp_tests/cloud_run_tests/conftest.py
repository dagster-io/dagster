from contextlib import contextmanager
from typing import Callable, ContextManager, Iterator
from unittest.mock import Mock, patch

import pytest
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import ExternalJob
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import in_process_test_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceRequestContext

from dagster_gcp_tests.cloud_run_tests import repo

IN_PROCESS_NAME = "<<in_process>>"


@pytest.fixture
def instance_cm() -> Callable[..., ContextManager[DagsterInstance]]:
    @contextmanager
    def cm(config=None):
        overrides = {
            "run_launcher": {
                "module": "dagster_gcp.cloud_run.run_launcher",
                "class": "CloudRunRunLauncher",
                "config": config or {},
            }
        }
        with instance_for_test(overrides) as dagster_instance:
            yield dagster_instance

    return cm


@pytest.fixture
def instance(
    instance_cm: Callable[..., ContextManager[DagsterInstance]],
) -> Iterator[DagsterInstance]:
    with instance_cm(
        {
            "project": "test_project",
            "region": "test_region",
            "job_name_by_code_location": {IN_PROCESS_NAME: "test_job_name"},
            "run_job_retry": {"wait": 1, "timeout": 60},
        }
    ) as dagster_instance:
        yield dagster_instance


@pytest.fixture
def workspace(instance: DagsterInstance) -> Iterator[WorkspaceRequestContext]:
    with in_process_test_workspace(
        instance,
        loadable_target_origin=LoadableTargetOrigin(
            python_file=repo.__file__,
            attribute=repo.repository.name,
        ),
        container_image="dagster:latest",
    ) as workspace:
        yield workspace


@pytest.fixture
def job() -> JobDefinition:
    return repo.job


@pytest.fixture
def external_job(workspace: WorkspaceRequestContext) -> ExternalJob:
    location = workspace.get_code_location(workspace.code_location_names[0])
    return location.get_repository(repo.repository.name).get_full_external_job(repo.job.name)


@pytest.fixture
def run(instance: DagsterInstance, job: JobDefinition, external_job: ExternalJob) -> DagsterRun:
    return instance.create_run_for_job(
        job,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
    )


@pytest.fixture
def executions():
    return {}


@pytest.fixture
def mock_jobs_client(executions):
    with patch("google.cloud.run_v2.JobsClient") as MockJobsClient:
        mock_jobs_client = MockJobsClient.return_value
        operation = Mock()
        operation.metadata.name = "projects/test_project/locations/test_region/jobs/test_job_name/executions/test_execution_id"
        mock_jobs_client.run_job.return_value = operation

        mock_execution = Mock(
            reconciling=True, succeeded_count=0, failed_count=0, cancelled_count=0
        )
        executions["test_execution_id"] = mock_execution
        yield mock_jobs_client


@pytest.fixture
def mock_executions_client(executions):
    with patch("google.cloud.run_v2.ExecutionsClient") as MockExecutionsClient:
        mock_executions_client = MockExecutionsClient.return_value

        def cancel_execution(request):
            execution_id = request.name.split("/")[-1]
            executions[execution_id].reconciling = False
            executions[execution_id].cancelled_count = 1

        def get_execution(request):
            execution_id = request.name.split("/")[-1]
            return executions[execution_id]

        mock_executions_client.cancel_execution.side_effect = cancel_execution
        mock_executions_client.get_execution.side_effect = get_execution

        yield mock_executions_client
