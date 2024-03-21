# pyright: reportPrivateImportUsage=false

import pendulum
import pytest
from dagster import (
    AssetCheckKey,
    AssetKey,
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness_checks.non_partitioned import (
    build_freshness_checks_for_non_partitioned_assets,
)
from dagster._core.definitions.freshness_checks.sensor import (
    FreshnessCheckSensorCursor,
    build_sensor_for_freshness_checks,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._serdes.serdes import deserialize_value
from dagster._seven.compat.pendulum import pendulum_freeze_time


def test_params() -> None:
    """Test the resulting sensor / error from different parameterizations of the builder function."""

    @asset
    def my_asset():
        pass

    checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset], maximum_lag_minutes=10
    )

    # Only essential params
    result = build_sensor_for_freshness_checks(
        freshness_checks=checks,
    )
    assert result.name == "freshness_checks_sensor"

    # All params (valid)
    result = build_sensor_for_freshness_checks(
        freshness_checks=checks, minimum_interval_seconds=10, name="my_sensor"
    )

    # Duplicate checks
    with pytest.raises(CheckError, match="duplicate asset checks"):
        build_sensor_for_freshness_checks(
            freshness_checks=[*checks, *checks],
        )

    # Invalid interval
    with pytest.raises(CheckError, match="Interval must be a positive integer"):
        build_sensor_for_freshness_checks(
            freshness_checks=checks,
            minimum_interval_seconds=-1,
        )


def test_maximum_lag_minutes() -> None:
    """Test the case where we have an asset partitioned with a maximum lag. Ensure that the sensor
    provides expected run requests in all cases.
    """

    @asset
    def my_asset():
        pass

    @asset
    def my_other_asset():
        pass

    ten_minute_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_asset], maximum_lag_minutes=10
    )
    twenty_minute_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_other_asset], maximum_lag_minutes=20
    )

    sensor = build_sensor_for_freshness_checks(
        freshness_checks=[*ten_minute_checks, *twenty_minute_checks],
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_asset, my_other_asset],
        asset_checks=[*ten_minute_checks, *twenty_minute_checks],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    # First evaluation, we should get run requests for both checks
    freeze_datetime = pendulum.now("UTC")
    with pendulum_freeze_time(freeze_datetime):
        run_request = sensor(context)
        assert isinstance(run_request, RunRequest)
        assert run_request.asset_check_keys == [
            AssetCheckKey(AssetKey("my_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_other_asset"), "freshness_check"),
        ]
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

    # Advance time within the maximum_lag_minutes window, and ensure we don't get a run_request.
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

    # Advance time past the maximum_lag_minutes window for the first asset, and ensure we get a run_request.
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

    utc_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_utc_asset], freshness_cron="0 0 * * *", maximum_lag_minutes=10
    )
    behind_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_behind_asset],
        freshness_cron="0 0 * * *",
        maximum_lag_minutes=10,
        freshness_cron_timezone="Etc/GMT-5",
    )
    ahead_checks = build_freshness_checks_for_non_partitioned_assets(
        assets=[my_ahead_asset],
        freshness_cron="0 0 * * *",
        maximum_lag_minutes=10,
        freshness_cron_timezone="Etc/GMT+5",
    )

    sensor = build_sensor_for_freshness_checks(
        freshness_checks=[*utc_checks, *behind_checks, *ahead_checks],
    )

    defs = Definitions(
        sensors=[sensor],
        assets=[my_utc_asset, my_behind_asset, my_ahead_asset],
        asset_checks=[*utc_checks, *behind_checks, *ahead_checks],
    )

    context = build_sensor_context(
        definitions=defs,
    )

    # First evaluation, we should get a run request
    freeze_datetime = pendulum.datetime(2022, 1, 1, 0, 0, 0, tz="UTC")
    with pendulum_freeze_time(freeze_datetime):
        run_request = sensor(context)
        assert isinstance(run_request, RunRequest)
        assert run_request.asset_check_keys == [
            AssetCheckKey(AssetKey("my_utc_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_behind_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_ahead_asset"), "freshness_check"),
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
        assert result.asset_check_keys == [
            AssetCheckKey(AssetKey("my_behind_asset"), "freshness_check"),
            AssetCheckKey(AssetKey("my_ahead_asset"), "freshness_check"),
        ]
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
