# pyright: reportPrivateImportUsage=false

import datetime

import pendulum
import pytest
from dagster import (
    AssetCheckKey,
    AssetKey,
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness_checks.last_update import (
    build_last_update_freshness_checks,
)
from dagster._core.definitions.freshness_checks.sensor import (
    FreshnessCheckSensorCursor,
    build_sensor_for_freshness_checks,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.sensor_definition import SensorDefinition, build_sensor_context
from dagster._serdes.serdes import deserialize_value
from dagster._seven.compat.pendulum import pendulum_freeze_time


def test_params() -> None:
    """Test the resulting sensor / error from different parameterizations of the builder function."""

    @asset
    def my_asset():
        pass

    check = build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    # Only essential params
    result = build_sensor_for_freshness_checks(
        freshness_checks=[check],
    )
    assert result.name == "freshness_checks_sensor"
    assert result.job_name == "freshness_checks_sensor_job"

    # All params (valid)
    result = build_sensor_for_freshness_checks(
        freshness_checks=[check], minimum_interval_seconds=10, name="my_sensor"
    )
    assert isinstance(result, SensorDefinition)

    # Duplicate checks
    with pytest.raises(CheckError, match="duplicate asset checks"):
        build_sensor_for_freshness_checks(
            freshness_checks=[check, check],
        )

    # Invalid interval
    with pytest.raises(CheckError, match="Interval must be a positive integer"):
        build_sensor_for_freshness_checks(
            freshness_checks=[check],
            minimum_interval_seconds=-1,
        )

    # Provide selection and checks list
    with pytest.raises(
        CheckError, match="Only one of freshness_checks or check_selection can be provided"
    ):
        build_sensor_for_freshness_checks(
            check_selection=AssetSelection.all_asset_checks(),
            freshness_checks=[check],
        )

    # Provide neither selection nor checks list
    with pytest.raises(
        CheckError, match="Exactly one of freshness_checks or check_selection must be provided"
    ):
        build_sensor_for_freshness_checks()

    # Check selection
    result = build_sensor_for_freshness_checks(
        check_selection=AssetSelection.all_asset_checks(),
    )
    assert isinstance(result, SensorDefinition)


def test_lower_bound_delta() -> None:
    """Test the case where we have an asset partitioned with a lower bound delta. Ensure that the sensor
    provides expected run requests in all cases.
    """

    @asset
    def my_asset():
        pass

    @asset
    def my_other_asset():
        pass

    ten_minute_check = build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )
    twenty_minute_check = build_last_update_freshness_checks(
        assets=[my_other_asset], lower_bound_delta=datetime.timedelta(minutes=20)
    )

    sensor = build_sensor_for_freshness_checks(
        freshness_checks=[ten_minute_check, twenty_minute_check],
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_asset, my_other_asset],
        asset_checks=[ten_minute_check, twenty_minute_check],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    # First evaluation, we should get run requests for both checks
    freeze_datetime = pendulum.now("UTC")
    with pendulum_freeze_time(freeze_datetime):
        run_request = sensor(context)
        assert isinstance(run_request, RunRequest)
        asset_check_keys = run_request.asset_check_keys
        assert asset_check_keys is not None
        assert set(asset_check_keys) == {
            AssetCheckKey(AssetKey("my_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_other_asset"), "freshness_check"),
        }
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(AssetKey("my_asset"), "freshness_check"): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_other_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
            }
        )

        # Run the sensor again, and ensure that we do not get a run request
        result = sensor(context)
        assert result is None
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(AssetKey("my_asset"), "freshness_check"): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_other_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
            }
        )

    # Advance time within the lower_bound_delta window, and ensure we don't get a run_request.
    freeze_datetime = freeze_datetime.add(minutes=5)
    with pendulum_freeze_time(freeze_datetime):
        result = sensor(context)
        assert result is None
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(AssetKey("my_asset"), "freshness_check"): freeze_datetime.subtract(
                    minutes=5
                ).timestamp(),
                AssetCheckKey(
                    AssetKey("my_other_asset"), "freshness_check"
                ): freeze_datetime.subtract(minutes=5).timestamp(),
            }
        )

    # Advance time past the lower_bound_delta window for the first asset, and ensure we get a run_request.
    freeze_datetime = freeze_datetime.add(minutes=6)
    with pendulum_freeze_time(freeze_datetime):
        result = sensor(context)
        assert isinstance(result, RunRequest)
        assert result.asset_check_keys == [AssetCheckKey(AssetKey("my_asset"), "freshness_check")]
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(AssetKey("my_asset"), "freshness_check"): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_other_asset"), "freshness_check"
                ): freeze_datetime.subtract(minutes=11).timestamp(),
            }
        )


def test_freshness_cron() -> None:
    """Test the case where we have a freshness cron and we have not executed, not passed the
    threshold time-wise, and then we have passed the threshold.
    """

    @asset
    def my_behind_asset():
        pass

    @asset
    def my_utc_asset():
        pass

    @asset
    def my_ahead_asset():
        pass

    utc_check = build_last_update_freshness_checks(
        assets=[my_utc_asset],
        deadline_cron="0 0 * * *",
        lower_bound_delta=datetime.timedelta(minutes=10),
    )
    behind_check = build_last_update_freshness_checks(
        assets=[my_behind_asset],
        deadline_cron="0 0 * * *",
        lower_bound_delta=datetime.timedelta(minutes=10),
        timezone="Etc/GMT-5",
    )
    ahead_check = build_last_update_freshness_checks(
        assets=[my_ahead_asset],
        deadline_cron="0 0 * * *",
        lower_bound_delta=datetime.timedelta(minutes=10),
        timezone="Etc/GMT+5",
    )

    sensor = build_sensor_for_freshness_checks(
        freshness_checks=[utc_check, behind_check, ahead_check],
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_utc_asset, my_behind_asset, my_ahead_asset],
        asset_checks=[utc_check, behind_check, ahead_check],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    # First evaluation, we should get a run request
    freeze_datetime = pendulum.datetime(2022, 1, 1, 0, 0, 0, tz="UTC")
    with pendulum_freeze_time(freeze_datetime):
        run_request = sensor(context)
        assert isinstance(run_request, RunRequest)
        asset_check_keys = run_request.asset_check_keys
        assert asset_check_keys is not None
        assert set(asset_check_keys) == {
            AssetCheckKey(AssetKey("my_utc_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_behind_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_ahead_asset"), "freshness_check"),
        }
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(
                    AssetKey("my_utc_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_behind_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_ahead_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
            }
        )

        # Run the sensor again, and ensure that we do not get a run request
        result = sensor(context)
        assert result is None
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(
                    AssetKey("my_utc_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_behind_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_ahead_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
            }
        )

    # Advance time past the freshness cron in GMT+5 and GMT-5. In both cases, we should have moved to a new tick of the cron.
    # Advance time 20 hours, since the cron is currently at 0:00 UTC (5:00 GMT+5).
    freeze_datetime = freeze_datetime.add(hours=20)
    with pendulum_freeze_time(freeze_datetime):
        result = sensor(context)
        assert isinstance(result, RunRequest)
        asset_check_keys = result.asset_check_keys
        assert asset_check_keys is not None
        assert set(asset_check_keys) == {
            AssetCheckKey(AssetKey("my_behind_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_ahead_asset"), "freshness_check"),
        }
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(
                    AssetKey("my_utc_asset"), "freshness_check"
                ): freeze_datetime.subtract(hours=20).timestamp(),
                AssetCheckKey(
                    AssetKey("my_behind_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_ahead_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
            }
        )

    # Advance time past the freshness cron in UTC. Ensure we get a new run request only for the UTC
    # asset.
    freeze_datetime = freeze_datetime.add(hours=5)
    with pendulum_freeze_time(freeze_datetime):
        result = sensor(context)
        assert isinstance(result, RunRequest)
        assert result.asset_check_keys == [
            AssetCheckKey(AssetKey("my_utc_asset"), "freshness_check")
        ]
        assert context.cursor
        cursor = deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        assert cursor == FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key={
                AssetCheckKey(
                    AssetKey("my_utc_asset"), "freshness_check"
                ): freeze_datetime.timestamp(),
                AssetCheckKey(
                    AssetKey("my_behind_asset"), "freshness_check"
                ): freeze_datetime.subtract(hours=5).timestamp(),
                AssetCheckKey(
                    AssetKey("my_ahead_asset"), "freshness_check"
                ): freeze_datetime.subtract(hours=5).timestamp(),
            }
        )


def test_runtime_selection_error() -> None:
    """Test the case where we have a runtime error in the selection function."""

    # Case where we select a non-freshness asset check
    @asset
    def my_asset():
        pass

    check = build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    @asset_check(asset=my_asset)
    def non_freshness_check() -> AssetCheckResult:
        return AssetCheckResult(passed=True)

    sensor = build_sensor_for_freshness_checks(
        check_selection=AssetSelection.all_asset_checks(),
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_asset],
        asset_checks=[check, non_freshness_check],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    with pytest.raises(
        CheckError, match="my_asset:non_freshness_check didn't have expected metadata."
    ):
        sensor(context)

    # Case where we select an asset instead of a check. We fail with a check error, since a
    # non-freshness check has been selected.
    sensor = build_sensor_for_freshness_checks(
        check_selection=AssetSelection.assets(my_asset),
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_asset],
        asset_checks=[check, non_freshness_check],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    with pytest.raises(
        CheckError, match="my_asset:non_freshness_check didn't have expected metadata."
    ):
        sensor(context)
