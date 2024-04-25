# pyright: reportPrivateImportUsage=false

import datetime

import pendulum
import pytest
from dagster import (
    AssetCheckKey,
    AssetKey,
    DagsterInstance,
    asset,
)
from dagster._check import CheckError
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness_checks.last_update import (
    build_last_update_freshness_checks,
)
from dagster._core.definitions.freshness_checks.sensor import (
    build_sensor_for_freshness_checks,
)
from dagster._core.definitions.freshness_checks.utils import (
    FRESH_UNTIL_METADATA_KEY,
)
from dagster._core.definitions.metadata import FloatMetadataValue
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.sensor_definition import build_sensor_context
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

    # All params (valid)
    result = build_sensor_for_freshness_checks(
        freshness_checks=[check], minimum_interval_seconds=10, name="my_sensor"
    )

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


def test_sensor_multi_asset_different_states(
    instance: DagsterInstance, pendulum_aware_report_dagster_event: None
) -> None:
    """Test the case where we have multiple assets in the same multi asset in different states. Ensure that the sensor
    handles each state correctly.
    """

    @multi_asset(
        outs={
            "never_eval": AssetOut(),
            "failed_eval": AssetOut(),
            "success_eval_unexpired": AssetOut(),
            "success_eval_expired": AssetOut(),
        },
    )
    def my_asset():
        pass

    freshness_checks = build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    freeze_time = pendulum.now("UTC")
    with pendulum_freeze_time(freeze_time):
        instance.report_runless_asset_event(
            AssetCheckEvaluation(
                asset_key=AssetKey("failed_eval"),
                check_name="freshness_check",
                passed=False,
                metadata={},
            )
        )
        instance.report_runless_asset_event(
            AssetCheckEvaluation(
                asset_key=AssetKey("success_eval_expired"),
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: FloatMetadataValue(
                        freeze_time.subtract(minutes=5).timestamp()
                    )
                },
            )
        )
        instance.report_runless_asset_event(
            AssetCheckEvaluation(
                asset_key=AssetKey("success_eval_unexpired"),
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: FloatMetadataValue(
                        freeze_time.add(minutes=5).timestamp()
                    )
                },
            )
        )

        sensor = build_sensor_for_freshness_checks(
            freshness_checks=[freshness_checks],
        )
        defs = Definitions(
            asset_checks=[freshness_checks],
            assets=[my_asset],
            sensors=[sensor],
        )

        context = build_sensor_context(
            instance=instance,
            definitions=defs,
        )

        # Upon evaluation, we should get a run request for never_eval and success_eval_expired.
        run_request = sensor(context)
        assert isinstance(run_request, RunRequest)
        assert run_request.asset_check_keys == [
            AssetCheckKey(AssetKey("never_eval"), "freshness_check"),
            AssetCheckKey(AssetKey("success_eval_expired"), "freshness_check"),
        ]
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None
