from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import RunStatus
from dagster_rest_resources.__generated__.get_run import (
    GetRun,
    GetRunRunOrErrorPythonError,
    GetRunRunOrErrorRun,
    GetRunRunOrErrorRunNotFoundError,
)
from dagster_rest_resources.__generated__.input_types import RunsFilter
from dagster_rest_resources.__generated__.list_runs import (
    ListRuns,
    ListRunsRunsOrErrorInvalidPipelineRunsFilterError,
    ListRunsRunsOrErrorPythonError,
    ListRunsRunsOrErrorRuns,
    ListRunsRunsOrErrorRunsResults,
)
from dagster_rest_resources.api.run import DgApiRun, DgApiRunApi, DgApiRunList
from dagster_rest_resources.gql_client import DagsterPlusGraphqlError, IGraphQLClient


def _make_run_result(
    run_id: str = "run-1",
    status: RunStatus = RunStatus.SUCCESS,
    creation_time: float = 1705311000.0,
    start_time: float | None = None,
    end_time: float | None = None,
    job_name: str = "test-job-1",
) -> GetRunRunOrErrorRun:
    return GetRunRunOrErrorRun(
        __typename="Run",
        runId=run_id,
        status=status,
        creationTime=creation_time,
        startTime=start_time,
        endTime=end_time,
        jobName=job_name,
    )


class TestGetRun:
    def test_returns_run(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(runOrError=_make_run_result())
        result = DgApiRunApi(client).get_run("run-1")

        client.get_run.assert_called_once_with(run_id="run-1")
        assert result == DgApiRun(
            id="run-1",
            status=RunStatus.SUCCESS,
            created_at=1705311000.0,
            started_at=None,
            ended_at=None,
            job_name="test-job-1",
        )

    def test_run_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorRunNotFoundError(__typename="RunNotFoundError", message="")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Run not found"):
            DgApiRunApi(client).get_run("run-xyz")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorPythonError(__typename="PythonError", message="")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching run"):
            DgApiRunApi(client).get_run("run-xyz")


def _make_list_run_result(
    run_id: str = "run-1",
    status: RunStatus = RunStatus.SUCCESS,
    creation_time: float = 1705311000.0,
    start_time: float | None = None,
    end_time: float | None = None,
    job_name: str = "test-job-1",
) -> ListRunsRunsOrErrorRunsResults:
    return ListRunsRunsOrErrorRunsResults(
        runId=run_id,
        status=status,
        creationTime=creation_time,
        startTime=start_time,
        endTime=end_time,
        jobName=job_name,
    )


class TestListRuns:
    def test_returns_runs(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorRuns(
                __typename="Runs",
                results=[
                    _make_list_run_result(run_id="r1"),
                    _make_list_run_result(run_id="r2"),
                ],
                count=2,
            )
        )
        result = DgApiRunApi(client).list_runs(
            limit=10,
            cursor="run-99",
            statuses=[RunStatus.SUCCESS, RunStatus.FAILURE],
            job_name="my_job",
        )

        client.list_runs.assert_called_once_with(
            filter=RunsFilter(
                statuses=[RunStatus.SUCCESS, RunStatus.FAILURE],
                pipelineName="my_job",
            ),
            cursor="run-99",
            limit=10,
        )
        assert len(result.items) == 2
        assert result.items[0].id == "r1"
        assert result.items[1].id == "r2"
        assert result.total == 2

    def test_returns_empty_list(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorRuns(__typename="Runs", results=[], count=0)
        )
        result = DgApiRunApi(client).list_runs()

        assert result == DgApiRunList(items=[], total=0)

    def test_no_filter_when_no_statuses_or_job_name(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorRuns(__typename="Runs", results=[], count=0)
        )
        DgApiRunApi(client).list_runs()

        client.list_runs.assert_called_once_with(filter=None, cursor=None, limit=50)

    def test_invalid_filter_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorInvalidPipelineRunsFilterError(
                __typename="InvalidPipelineRunsFilterError",
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Invalid runs filter"):
            DgApiRunApi(client).list_runs()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorPythonError(__typename="PythonError", message="")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching runs"):
            DgApiRunApi(client).list_runs()
