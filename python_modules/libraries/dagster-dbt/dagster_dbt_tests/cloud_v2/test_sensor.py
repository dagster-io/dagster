from datetime import datetime, timezone
from unittest.mock import patch

import responses
from dagster import DagsterInstance, SensorResult, build_sensor_context
from dagster._core.test_utils import freeze_time
from dagster._serdes import deserialize_value
from dagster_dbt.cloud_v2.sensor_builder import DbtCloudPollingSensorCursor

from dagster_dbt_tests.cloud_v2.conftest import (
    SAMPLE_EMPTY_BATCH_LIST_RUNS_RESPONSE,
    TEST_REST_API_BASE_URL,
    TEST_RUN_URL,
    build_and_invoke_sensor,
    fully_loaded_repo_from_dbt_cloud_workspace,
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
