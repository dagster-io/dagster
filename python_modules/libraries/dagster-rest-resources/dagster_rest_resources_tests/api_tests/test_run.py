from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import EvaluationErrorReason, RunStatus
from dagster_rest_resources.__generated__.get_run import (
    GetRun,
    GetRunRunOrErrorPythonError,
    GetRunRunOrErrorRun,
    GetRunRunOrErrorRunNotFoundError,
)
from dagster_rest_resources.__generated__.input_types import (
    AssetKeyInput,
    ExecutionMetadata,
    ExecutionParams,
    ExecutionTag,
    JobOrPipelineSelector,
    RunsFilter,
)
from dagster_rest_resources.__generated__.launch_run import (
    LaunchRun,
    LaunchRunLaunchRunConflictingExecutionParamsError,
    LaunchRunLaunchRunInvalidOutputError,
    LaunchRunLaunchRunInvalidStepError,
    LaunchRunLaunchRunInvalidSubsetError,
    LaunchRunLaunchRunLaunchRunSuccess,
    LaunchRunLaunchRunLaunchRunSuccessRun,
    LaunchRunLaunchRunNoModeProvidedError,
    LaunchRunLaunchRunPipelineNotFoundError,
    LaunchRunLaunchRunPresetNotFoundError,
    LaunchRunLaunchRunPythonError,
    LaunchRunLaunchRunRunConfigValidationInvalid,
    LaunchRunLaunchRunRunConfigValidationInvalidErrors,
    LaunchRunLaunchRunRunConflict,
    LaunchRunLaunchRunUnauthorizedError,
)
from dagster_rest_resources.__generated__.list_runs import (
    ListRuns,
    ListRunsRunsOrErrorInvalidPipelineRunsFilterError,
    ListRunsRunsOrErrorPythonError,
    ListRunsRunsOrErrorRuns,
    ListRunsRunsOrErrorRunsResults,
)
from dagster_rest_resources.api.run import (
    PARTITION_TAG,
    DgApiRun,
    DgApiRunApi,
    DgApiRunLaunchResult,
    DgApiRunList,
)
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


def _make_launch_success(run_id: str = "run-1") -> LaunchRun:
    return LaunchRun(
        launchRun=LaunchRunLaunchRunLaunchRunSuccess(
            __typename="LaunchRunSuccess",
            run=LaunchRunLaunchRunLaunchRunSuccessRun(
                runId=run_id,
                status=RunStatus.STARTED,
            ),
        )
    )


def _launch_args(**overrides) -> dict:
    defaults = dict(
        location_name="loc",
        repository_name="__repository__",
        job_name="my_job",
        asset_keys=None,
        tags=None,
        run_config=None,
        partition=None,
    )
    defaults.update(overrides)
    return defaults


class TestLaunchRun:
    def test_launches_job_only(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = _make_launch_success()

        result = DgApiRunApi(client).create_run(**_launch_args())

        client.launch_run.assert_called_once_with(
            execution_params=ExecutionParams(
                selector=JobOrPipelineSelector(
                    repositoryLocationName="loc",
                    repositoryName="__repository__",
                    jobName="my_job",
                    assetSelection=None,
                ),
                runConfigData=None,
                executionMetadata=None,
            )
        )
        assert result == DgApiRunLaunchResult(run_id="run-1", status=RunStatus.STARTED)

    def test_launches_with_asset_keys(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = _make_launch_success()

        DgApiRunApi(client).create_run(
            **_launch_args(
                job_name=None,
                asset_keys=["raw_customers", "marts/dim_customers"],
            )
        )

        call_params: ExecutionParams = client.launch_run.call_args.kwargs["execution_params"]
        assert call_params.selector.asset_selection == [
            AssetKeyInput(path=["raw_customers"]),
            AssetKeyInput(path=["marts", "dim_customers"]),
        ]
        assert call_params.selector.job_name is None

    def test_launches_with_partition_adds_tag(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = _make_launch_success()

        DgApiRunApi(client).create_run(**_launch_args(partition="2026-05-15"))

        call_params: ExecutionParams = client.launch_run.call_args.kwargs["execution_params"]
        assert call_params.execution_metadata == ExecutionMetadata(
            tags=[ExecutionTag(key=PARTITION_TAG, value="2026-05-15")]
        )

    def test_launches_with_user_tags_and_partition(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = _make_launch_success()

        DgApiRunApi(client).create_run(
            **_launch_args(
                tags={"team": "data", "purpose": "smoke"},
                partition="2026-05-15",
            )
        )

        call_params: ExecutionParams = client.launch_run.call_args.kwargs["execution_params"]
        assert call_params.execution_metadata is not None
        tags = call_params.execution_metadata.tags
        assert tags == [
            ExecutionTag(key="team", value="data"),
            ExecutionTag(key="purpose", value="smoke"),
            ExecutionTag(key=PARTITION_TAG, value="2026-05-15"),
        ]

    def test_launches_with_run_config(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = _make_launch_success()

        DgApiRunApi(client).create_run(**_launch_args(run_config={"ops": {"foo": {"config": 1}}}))

        call_params: ExecutionParams = client.launch_run.call_args.kwargs["execution_params"]
        assert call_params.run_config_data == {"ops": {"foo": {"config": 1}}}

    def test_raises_when_neither_job_nor_assets(self):
        client = Mock(spec=IGraphQLClient)
        with pytest.raises(DagsterPlusGraphqlError, match="At least one of"):
            DgApiRunApi(client).create_run(**_launch_args(job_name=None, asset_keys=None))
        client.launch_run.assert_not_called()

    def test_run_config_validation_invalid_raises_with_messages(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = LaunchRun(
            launchRun=LaunchRunLaunchRunRunConfigValidationInvalid(
                __typename="RunConfigValidationInvalid",
                pipelineName="my_job",
                errors=[
                    LaunchRunLaunchRunRunConfigValidationInvalidErrors(
                        __typename="MissingFieldConfigError",
                        message="Missing required field: foo",
                        reason=EvaluationErrorReason.MISSING_REQUIRED_FIELD,
                    ),
                    LaunchRunLaunchRunRunConfigValidationInvalidErrors(
                        __typename="RuntimeMismatchConfigError",
                        message="Expected int, got str",
                        reason=EvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                    ),
                ],
            )
        )
        with pytest.raises(
            DagsterPlusGraphqlError,
            match=r"(?s)Invalid run config.*Missing required field.*Expected int",
        ):
            DgApiRunApi(client).create_run(**_launch_args())

    def test_pipeline_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = LaunchRun(
            launchRun=LaunchRunLaunchRunPipelineNotFoundError(
                __typename="PipelineNotFoundError",
                message="job `missing` not found",
                pipelineName="missing",
                repositoryName="__repository__",
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Job not found"):
            DgApiRunApi(client).create_run(**_launch_args(job_name="missing"))

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = LaunchRun(
            launchRun=LaunchRunLaunchRunUnauthorizedError(
                __typename="UnauthorizedError", message="forbidden"
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Unauthorized"):
            DgApiRunApi(client).create_run(**_launch_args())

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = LaunchRun(
            launchRun=LaunchRunLaunchRunPythonError(__typename="PythonError", message="boom")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error launching run"):
            DgApiRunApi(client).create_run(**_launch_args())

    @pytest.mark.parametrize(
        "error_obj, match",
        [
            (
                LaunchRunLaunchRunInvalidStepError(
                    __typename="InvalidStepError", invalidStepKey="bad_step"
                ),
                "Invalid step key.*bad_step",
            ),
            (
                LaunchRunLaunchRunInvalidOutputError(
                    __typename="InvalidOutputError", stepKey="s", invalidOutputName="o"
                ),
                "Invalid output `o` on step `s`",
            ),
            (
                LaunchRunLaunchRunInvalidSubsetError(
                    __typename="InvalidSubsetError", message="bad subset"
                ),
                "Invalid subset",
            ),
            (
                LaunchRunLaunchRunPresetNotFoundError(
                    __typename="PresetNotFoundError", message="missing", preset="p"
                ),
                "Preset not found",
            ),
            (
                LaunchRunLaunchRunConflictingExecutionParamsError(
                    __typename="ConflictingExecutionParamsError", message="conflict"
                ),
                "Conflicting execution params",
            ),
            (
                LaunchRunLaunchRunNoModeProvidedError(
                    __typename="NoModeProvidedError", message="no mode", pipelineName="my_job"
                ),
                "No mode provided",
            ),
            (
                LaunchRunLaunchRunRunConflict(__typename="RunConflict", message="dup"),
                "Run conflict",
            ),
        ],
    )
    def test_other_error_types_raise(self, error_obj, match):
        client = Mock(spec=IGraphQLClient)
        client.launch_run.return_value = LaunchRun(launchRun=error_obj)
        with pytest.raises(DagsterPlusGraphqlError, match=match):
            DgApiRunApi(client).create_run(**_launch_args())
