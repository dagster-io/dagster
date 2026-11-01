from collections.abc import Mapping
from unittest import mock

import pytest
from dagster import AssetExecutionContext, asset, materialize
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.pipes.utils import PipesTempFileContextInjector, PipesTempFileMessageReader
from dagster_databricks.pipes import (
    PipesDatabricksClient,
    PipesDatabricksServerlessClient,
    PipesDbfsContextInjector,
    PipesDbfsMessageReader,
    PipesUnityCatalogVolumesContextInjector,
    PipesUnityCatalogVolumesMessageReader,
)
from dagster_pipes import (
    PipesContext,
    PipesDefaultContextLoader,
    PipesDefaultMessageWriter,
    PipesMappingParamsLoader,
)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

JOB_ID = 123
RUN_ID = 456


def _run(
    life_cycle_state: jobs.RunLifeCycleState,
    result_state: jobs.RunResultState | None = None,
) -> jobs.Run:
    return jobs.Run(
        run_id=RUN_ID,
        run_page_url=f"https://test.databricks.com/jobs/{JOB_ID}/runs/{RUN_ID}",
        state=jobs.RunState(life_cycle_state=life_cycle_state, result_state=result_state),
    )


def _fake_run_now(job_id: int, job_parameters: Mapping[str, str], **kwargs) -> mock.MagicMock:
    # Stand-in for a Databricks notebook task reading the job parameters as widgets. Builds the
    # context directly since `open_dagster_pipes` reuses a process-wide singleton across tests.
    with PipesContext(
        params_loader=PipesMappingParamsLoader(job_parameters),
        context_loader=PipesDefaultContextLoader(),
        message_writer=PipesDefaultMessageWriter(),
    ) as pipes:
        pipes.report_asset_materialization(metadata={"value": 42})
    return mock.MagicMock(run_id=RUN_ID)


@pytest.fixture
def workspace_client() -> mock.MagicMock:
    client = mock.MagicMock(spec=WorkspaceClient)
    client.jobs.run_now.side_effect = _fake_run_now
    client.jobs.get_run.return_value = _run(
        jobs.RunLifeCycleState.TERMINATED, jobs.RunResultState.SUCCESS
    )
    return client


def _make_client(workspace_client: mock.MagicMock) -> PipesDatabricksServerlessClient:
    return PipesDatabricksServerlessClient(
        client=workspace_client,
        volume_path="/Volumes/test/tmp",
        context_injector=PipesTempFileContextInjector(),
        message_reader=PipesTempFileMessageReader(),
        poll_interval_seconds=0,
    )


def _materialize(pipes_client, **run_job_kwargs):
    @asset
    def databricks_job_asset(context: AssetExecutionContext):
        return pipes_client.run_job(
            context=context, job_id=JOB_ID, **run_job_kwargs
        ).get_materialize_result()

    return materialize([databricks_job_asset], raise_on_error=False)


def test_run_job_reports_messages(workspace_client: mock.MagicMock):
    result = _materialize(
        _make_client(workspace_client),
        job_parameters={"user_param": "value"},
        run_now_args={"only": ["task_a"], "performance_target": jobs.PerformanceTarget.STANDARD},
    )
    assert result.success

    run_now_kwargs = workspace_client.jobs.run_now.call_args.kwargs
    assert run_now_kwargs["job_id"] == JOB_ID
    assert set(run_now_kwargs["job_parameters"]) == {
        "user_param",
        "DAGSTER_PIPES_CONTEXT",
        "DAGSTER_PIPES_MESSAGES",
    }
    assert run_now_kwargs["only"] == ["task_a"]
    assert run_now_kwargs["performance_target"] == jobs.PerformanceTarget.STANDARD

    metadata = result.asset_materializations_for_node("databricks_job_asset")[0].metadata
    assert metadata["value"].value == 42
    assert metadata["Databricks Job Run ID"].value == str(RUN_ID)


def test_run_job_failed_run(workspace_client: mock.MagicMock):
    workspace_client.jobs.get_run.return_value = _run(
        jobs.RunLifeCycleState.TERMINATED, jobs.RunResultState.FAILED
    )
    assert not _materialize(_make_client(workspace_client)).success


@pytest.mark.parametrize(
    "run_job_kwargs",
    [
        {"job_parameters": {"DAGSTER_PIPES_CONTEXT": "user-value"}},
        {"run_now_args": {"job_parameters": {"user_param": "value"}}},
    ],
    ids=["reserved_job_parameter", "job_parameters_in_run_now_args"],
)
def test_run_job_rejects_invalid_parameters(workspace_client: mock.MagicMock, run_job_kwargs):
    assert not _materialize(_make_client(workspace_client), **run_job_kwargs).success
    workspace_client.jobs.run_now.assert_not_called()


def test_run_job_forwards_termination(workspace_client: mock.MagicMock):
    workspace_client.jobs.get_run.side_effect = [
        DagsterExecutionInterruptedError(),
        _run(jobs.RunLifeCycleState.TERMINATED, jobs.RunResultState.CANCELED),
    ]
    assert not _materialize(_make_client(workspace_client)).success
    workspace_client.jobs.cancel_run.assert_called_once_with(RUN_ID)


@pytest.mark.parametrize(
    "pipes_client_cls, expected_injector, expected_reader",
    [
        (PipesDatabricksClient, PipesDbfsContextInjector, PipesDbfsMessageReader),
        (
            PipesDatabricksServerlessClient,
            PipesUnityCatalogVolumesContextInjector,
            PipesUnityCatalogVolumesMessageReader,
        ),
    ],
)
def test_run_job_default_injector_and_reader(
    workspace_client: mock.MagicMock, pipes_client_cls, expected_injector, expected_reader
):
    kwargs = (
        {"volume_path": "/Volumes/test/tmp"}
        if pipes_client_cls is PipesDatabricksServerlessClient
        else {}
    )
    pipes_client = pipes_client_cls(client=workspace_client, **kwargs)
    with mock.patch.object(pipes_client_cls, "_run_job_and_poll") as run_job_and_poll:
        pipes_client.run_job(context=mock.MagicMock(), job_id=JOB_ID)

    call_kwargs = run_job_and_poll.call_args.kwargs
    assert isinstance(call_kwargs["context_injector"], expected_injector)
    assert isinstance(call_kwargs["message_reader"], expected_reader)
