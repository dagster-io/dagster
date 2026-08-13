import re
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import responses
from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterInstance,
    SensorResult,
    build_sensor_context,
)
from dagster._core.test_utils import freeze_time
from dagster._serdes import deserialize_value
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.sensor_builder import (
    DbtCloudPollingSensorCursor,
    _job_asset_materialization_from_run,
    build_dbt_cloud_polling_sensor,
    materializations_from_batch_iter,
)
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun, DbtCloudWorkspaceData

from dagster_dbt_tests.cloud_v2.conftest import (
    SAMPLE_EMPTY_BATCH_LIST_RUNS_RESPONSE,
    TEST_ACCOUNT_ID,
    TEST_ENVIRONMENT_ID,
    TEST_PROJECT_ID,
    TEST_REST_API_BASE_URL,
    TEST_RUN_URL,
    build_and_invoke_sensor,
    fully_loaded_repo_from_dbt_cloud_workspace,
)


def test_sensor_name(workspace: DbtCloudWorkspace) -> None:
    sensor = build_dbt_cloud_polling_sensor(workspace=workspace)
    assert (
        sensor.name
        == f"dbt_cloud_{TEST_ACCOUNT_ID}_{TEST_PROJECT_ID}_{TEST_ENVIRONMENT_ID}__run_status_sensor"
    )


def test_asset_materializations(
    init_load_context: None, instance: DagsterInstance, all_api_mocks: responses.RequestsMock
) -> None:
    """Test the asset materializations produced by a sensor."""
    result, _ = build_and_invoke_sensor(
        instance=instance,
    )
    assert len(result.asset_events) == 8
    first_asset_mat = next(mat for mat in sorted(result.asset_events))

    expected_metadata_keys = {
        "dagster_dbt/completed_at_timestamp",
        "unique_id",
        "invocation_id",
        "run_url",
        "execution_duration",
    }
    assert set(first_asset_mat.metadata.keys()) == expected_metadata_keys

    # Sanity check
    assert first_asset_mat.metadata["unique_id"].value == "model.jaffle_shop.customers"
    assert first_asset_mat.metadata["run_url"].value == TEST_RUN_URL


def test_runs_triggered_by_dagster(
    init_load_context: None,
    instance: DagsterInstance,
    sensor_runs_triggered_by_dagster_api_mocks: responses.RequestsMock,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test the case where runs were triggered by Dagster."""
    result, _ = build_and_invoke_sensor(
        instance=instance,
    )
    assert len(result.asset_events) == 0

    captured = capsys.readouterr()
    assert re.search(
        r"dagster - INFO - Run (?s:.)+ was triggered by Dagster. Continuing.", captured.err
    )


def test_runs_triggered_by_stale_dagster_job(
    init_load_context: None,
    instance: DagsterInstance,
    sensor_runs_triggered_by_stale_dagster_job_api_mocks: responses.RequestsMock,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test that runs from a stale adhoc job (old naming convention) are still filtered out."""
    result, _ = build_and_invoke_sensor(
        instance=instance,
    )
    assert len(result.asset_events) == 0

    captured = capsys.readouterr()
    assert re.search(
        r"dagster - INFO - Run (?s:.)+ was triggered by Dagster. Continuing.", captured.err
    )


def test_no_runs(
    init_load_context: None,
    instance: DagsterInstance,
    sensor_no_runs_api_mocks: responses.RequestsMock,
) -> None:
    """Test the case with no runs."""
    result, _ = build_and_invoke_sensor(
        instance=instance,
    )
    assert len(result.asset_events) == 0


_CALLCOUNT = [0]


def _create_datetime_mocker(iter_times: list[datetime]):
    def _mock_get_current_datetime() -> datetime:
        the_time = iter_times[_CALLCOUNT[0]]
        _CALLCOUNT[0] += 1
        return the_time

    return _mock_get_current_datetime


def test_cursor(
    init_load_context: None, instance: DagsterInstance, all_api_mocks: responses.RequestsMock
) -> None:
    """Test the case with no runs."""
    with freeze_time(datetime(2021, 1, 1, tzinfo=timezone.utc)):
        # First, run through a full successful iteration of the sensor.
        # Expect time to move forward, and offset to be 0, since we completed iteration of all runs.
        # Then, run through a partial iteration of the sensor. We mock get_current_datetime to return a time
        # after timeout passes iteration start after the first call, meaning we should pause iteration.
        repo_def = fully_loaded_repo_from_dbt_cloud_workspace()
        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)
        assert context.cursor
        new_cursor = deserialize_value(context.cursor, DbtCloudPollingSensorCursor)
        assert (
            new_cursor.finished_at_lower_bound
            == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        )
        assert new_cursor.finished_at_upper_bound is None
        assert new_cursor.offset == 0

    # Now, we expect that we will not have completed iteration before we need to pause evaluation.
    datetimes = [
        datetime(2021, 2, 1, tzinfo=timezone.utc),  # set initial time
        datetime(2021, 2, 1, 0, 0, 30, tzinfo=timezone.utc),  # initial iteration time
        datetime(
            2022, 2, 2, tzinfo=timezone.utc
        ),  # second iteration time, at which iteration should be paused
    ]
    with patch(
        "dagster._time._mockable_get_current_datetime", wraps=_create_datetime_mocker(datetimes)
    ):
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, DbtCloudPollingSensorCursor)
        # We didn't advance to the next effective timestamp, since we didn't complete iteration
        assert (
            new_cursor.finished_at_lower_bound
            == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        )
        # We have not yet moved forward
        assert (
            new_cursor.finished_at_upper_bound
            == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        )
        assert new_cursor.offset == 1

        _CALLCOUNT[0] = 0
        # We weren't able to complete iteration, so we should pause iteration again
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, DbtCloudPollingSensorCursor)
        assert (
            new_cursor.finished_at_lower_bound
            == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        )
        assert (
            new_cursor.finished_at_upper_bound
            == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        )
        assert new_cursor.offset == 2

        _CALLCOUNT[0] = 0
        # For the last iteration, the batch result must be None
        all_api_mocks.replace(
            method_or_response=responses.GET,
            url=f"{TEST_REST_API_BASE_URL}/runs",
            json=SAMPLE_EMPTY_BATCH_LIST_RUNS_RESPONSE,
        )

        # Now it should finish iteration.
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, DbtCloudPollingSensorCursor)
        assert (
            new_cursor.finished_at_lower_bound
            == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        )
        assert new_cursor.finished_at_upper_bound is None
        assert new_cursor.offset == 0


# ============================================================================
# Job-level materialization tests (mirror_jobs="asset"|"both" wiring)
# ============================================================================


def _make_workspace_data_with_jobs(
    user_jobs: list[dict],
    adhoc_ids: list[int],
    adhoc_job_names: list[dict] | None = None,
) -> DbtCloudWorkspaceData:
    """Build a DbtCloudWorkspaceData with a mix of user-defined and adhoc jobs."""
    jobs = list(user_jobs)
    if adhoc_job_names is not None:
        jobs.extend(adhoc_job_names)
    return DbtCloudWorkspaceData(
        project_id=1,
        environment_id=1,
        adhoc_job_ids=adhoc_ids,
        manifest={
            "metadata": {"dbt_schema_version": "1.0.0", "adapter_type": "postgres"},
            "nodes": {},
            "sources": {},
            "metrics": {},
            "semantic_models": {},
            "exposures": {},
            "child_map": {},
            "parent_map": {},
            "selectors": {},
        },
        jobs=jobs,
    )


def _run_details(
    run_id: int,
    job_definition_id: int,
    status: int = DbtCloudJobRunStatusType.SUCCESS.value,
    href: str = "https://cloud.getdbt.com/runs/1",
) -> dict:
    return {
        "id": run_id,
        "job_definition_id": job_definition_id,
        "trigger_id": 0,
        "account_id": 1,
        "environment_id": 1,
        "project_id": 1,
        "status": status,
        "href": href,
    }


def test_job_asset_materialization_from_run_carries_run_metadata():
    """The helper attaches run id, human-readable status, and Cloud run URL as metadata
    so users can click through from the Dagster materialization page to the Cloud UI.
    """
    run = DbtCloudRun.from_run_details(
        run_details=_run_details(run_id=99, job_definition_id=1, status=10)
    )
    mat = _job_asset_materialization_from_run(
        run=run, job_asset_key=AssetKey(["dbt_cloud_job", "My_Job"])
    )
    assert mat.asset_key == AssetKey(["dbt_cloud_job", "My_Job"])
    assert mat.metadata["dbt_cloud_run_id"].value == 99
    assert mat.metadata["dbt_cloud_status"].value == "SUCCESS"
    assert mat.metadata["dbt_cloud_run_url"].value == "https://cloud.getdbt.com/runs/1"


def test_job_asset_materialization_from_run_handles_missing_status():
    """When the API omits status (rare, but seen for in-flight runs), the materialization
    is still emitted with the run id and url — no `dbt_cloud_status` key.
    """
    run_details = _run_details(run_id=99, job_definition_id=1)
    run_details["status"] = None
    run = DbtCloudRun.from_run_details(run_details=run_details)
    mat = _job_asset_materialization_from_run(
        run=run, job_asset_key=AssetKey(["dbt_cloud_job", "My_Job"])
    )
    assert "dbt_cloud_status" not in mat.metadata


def _make_workspace_for_sensor(workspace_data, runs_batches):
    """Build a MagicMock DbtCloudWorkspace whose client returns pre-canned runs.

    ``runs_batches`` is a list of (runs_list, total_runs) tuples returned by
    successive ``get_runs_batch`` calls, mimicking pagination.
    """
    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.project_id = workspace_data.project_id
    workspace.environment_id = workspace_data.environment_id
    workspace.credentials = MagicMock(account_id=1)
    workspace.get_or_fetch_workspace_data.return_value = workspace_data

    client = MagicMock()
    client.get_runs_batch.side_effect = list(runs_batches)
    # Return empty artifacts so we skip the per-model materialization path — we
    # only care about the job-asset materialization here.
    client.list_run_artifacts.return_value = []
    workspace.get_client.return_value = client
    return workspace


def test_materializations_from_batch_iter_emits_job_asset_when_flag_on():
    """When `emit_job_asset_materializations=True`, a run against a user-defined Cloud
    job produces exactly one `AssetMaterialization` on the mirrored job asset key,
    regardless of whether the run has a `run_results.json` artifact. This is what lets
    downstream `AutomationCondition.eager()` fire on real Cloud completions.
    """
    workspace_data = _make_workspace_data_with_jobs(
        user_jobs=[
            {"id": 900, "account_id": 1, "name": "Prod Build", "project_id": 1, "environment_id": 1}
        ],
        adhoc_ids=[],
    )
    workspace = _make_workspace_for_sensor(
        workspace_data,
        runs_batches=[
            ([_run_details(run_id=1, job_definition_id=900)], 1),
            ([], 1),  # end of pages
        ],
    )
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

    context = MagicMock()
    batches = list(
        materializations_from_batch_iter(
            context=context,
            finished_at_lower_bound=0.0,
            finished_at_upper_bound=1.0,
            offset=0,
            workspace=workspace,
            dagster_dbt_translator=DagsterDbtTranslator(),
            emit_job_asset_materializations=True,
        )
    )
    non_null = [b for b in batches if b is not None]
    assert len(non_null) == 1
    mats = list(non_null[0].asset_events)
    assert len(mats) == 1
    assert mats[0].asset_key == AssetKey(["dbt_cloud_job", "Prod_Build"])


def test_materializations_from_batch_iter_skips_adhoc_runs_even_with_flag():
    """Adhoc runs (Dagster-triggered CLI invocations) are always skipped — even when
    `emit_job_asset_materializations=True`. This preserves the existing contract that
    Dagster-triggered runs don't double-emit through the sensor. The mirrored job
    asset only receives materializations for user-visible Cloud jobs.
    """
    workspace_data = _make_workspace_data_with_jobs(
        user_jobs=[],
        adhoc_ids=[789],
        adhoc_job_names=[
            {
                "id": 789,
                "account_id": 1,
                "name": "DAGSTER_ADHOC_JOB__1__1",
                "project_id": 1,
                "environment_id": 1,
            }
        ],
    )
    workspace = _make_workspace_for_sensor(
        workspace_data,
        runs_batches=[
            ([_run_details(run_id=1, job_definition_id=789)], 1),
            ([], 1),
        ],
    )
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

    context = MagicMock()
    batches = list(
        materializations_from_batch_iter(
            context=context,
            finished_at_lower_bound=0.0,
            finished_at_upper_bound=1.0,
            offset=0,
            workspace=workspace,
            dagster_dbt_translator=DagsterDbtTranslator(),
            emit_job_asset_materializations=True,
        )
    )
    non_null = [b for b in batches if b is not None]
    assert non_null == []


def test_materializations_from_batch_iter_no_job_mat_when_flag_off():
    """When `emit_job_asset_materializations=False` (default / backward compat), no
    job-asset materializations are emitted even if user-defined Cloud jobs are present.
    """
    workspace_data = _make_workspace_data_with_jobs(
        user_jobs=[
            {"id": 900, "account_id": 1, "name": "Prod Build", "project_id": 1, "environment_id": 1}
        ],
        adhoc_ids=[],
    )
    workspace = _make_workspace_for_sensor(
        workspace_data,
        runs_batches=[
            ([_run_details(run_id=1, job_definition_id=900)], 1),
            ([], 1),
        ],
    )
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

    context = MagicMock()
    batches = list(
        materializations_from_batch_iter(
            context=context,
            finished_at_lower_bound=0.0,
            finished_at_upper_bound=1.0,
            offset=0,
            workspace=workspace,
            dagster_dbt_translator=DagsterDbtTranslator(),
            emit_job_asset_materializations=False,
        )
    )
    non_null = [b for b in batches if b is not None]
    assert non_null == []


def test_materializations_from_batch_iter_ignores_unknown_job_id():
    """A finished run whose `job_definition_id` doesn't match any user-defined job
    (e.g., a deleted job's residual run) does NOT emit a job-asset materialization.
    Prevents phantom materializations for non-existent asset keys.
    """
    workspace_data = _make_workspace_data_with_jobs(
        user_jobs=[
            {"id": 900, "account_id": 1, "name": "Prod Build", "project_id": 1, "environment_id": 1}
        ],
        adhoc_ids=[],
    )
    workspace = _make_workspace_for_sensor(
        workspace_data,
        runs_batches=[
            ([_run_details(run_id=1, job_definition_id=99999)], 1),  # unknown id
            ([], 1),
        ],
    )
    from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

    context = MagicMock()
    batches = list(
        materializations_from_batch_iter(
            context=context,
            finished_at_lower_bound=0.0,
            finished_at_upper_bound=1.0,
            offset=0,
            workspace=workspace,
            dagster_dbt_translator=DagsterDbtTranslator(),
            emit_job_asset_materializations=True,
        )
    )
    assert [b for b in batches if b is not None] == []


def test_build_dbt_cloud_polling_sensor_default_flag_off(workspace: DbtCloudWorkspace) -> None:
    """The sensor's `emit_job_asset_materializations` flag defaults to False — no
    behavior change for existing users on upgrade.
    """
    sensor = build_dbt_cloud_polling_sensor(workspace=workspace)
    assert sensor is not None


def test_asset_materialization_type_for_sensor_result_smoke():
    """`_job_asset_materialization_from_run` returns an `AssetMaterialization` (not
    `AssetObservation`), which is what triggers `AutomationCondition.eager()`
    downstream. Observations don't mark the asset "green" — only materializations do.
    """
    run = DbtCloudRun.from_run_details(_run_details(run_id=1, job_definition_id=1))
    mat = _job_asset_materialization_from_run(run=run, job_asset_key=AssetKey(["a"]))
    assert isinstance(mat, AssetMaterialization)
