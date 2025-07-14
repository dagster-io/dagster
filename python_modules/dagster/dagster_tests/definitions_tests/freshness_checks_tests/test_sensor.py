# pyright: reportPrivateImportUsage=false
import datetime
import time

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._check import CheckError
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluationPlanned,
)
from dagster._core.definitions.asset_checks.asset_check_factories.utils import (
    FRESH_UNTIL_METADATA_KEY,
)
from dagster._core.events import DagsterEventType
from dagster._core.storage.tags import SENSOR_NAME_TAG
from dagster._core.test_utils import create_run_for_test, freeze_time
from dagster._core.utils import make_new_run_id
from dagster._time import get_current_datetime


def test_params() -> None:
    """Test the resulting sensor / error from different parameterizations of the builder function."""

    @dg.asset
    def my_asset():
        pass

    check = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    # Only essential params
    result = dg.build_sensor_for_freshness_checks(freshness_checks=check)
    assert result.name == "freshness_checks_sensor"

    # All params (valid)
    result = dg.build_sensor_for_freshness_checks(
        freshness_checks=check, minimum_interval_seconds=10, name="my_sensor"
    )

    # Duplicate checks
    with pytest.raises(CheckError, match="duplicate asset checks"):
        dg.build_sensor_for_freshness_checks(freshness_checks=[*check, *check])

    # Invalid interval
    with pytest.raises(CheckError, match="Interval must be a positive integer"):
        dg.build_sensor_for_freshness_checks(freshness_checks=check, minimum_interval_seconds=-1)


def test_sensor_multi_asset_different_states(instance: DagsterInstance) -> None:
    """Test the case where we have multiple assets in the same multi asset in different states. Ensure that the sensor
    handles each state correctly.
    """

    @dg.multi_asset(
        outs={
            "never_eval": dg.AssetOut(),
            "failed_eval": dg.AssetOut(),
            "success_eval_unexpired": dg.AssetOut(),
            "success_eval_expired": dg.AssetOut(),
        },
    )
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    frozen_time = get_current_datetime()
    with freeze_time(frozen_time):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("failed_eval"),
                check_name="freshness_check",
                passed=False,
                metadata={},
            )
        )
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("success_eval_expired"),
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: dg.FloatMetadataValue(
                        (frozen_time - datetime.timedelta(minutes=5)).timestamp()
                    )
                },
            )
        )
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("success_eval_unexpired"),
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: dg.FloatMetadataValue(
                        (frozen_time + datetime.timedelta(minutes=5)).timestamp()
                    )
                },
            )
        )

        sensor = dg.build_sensor_for_freshness_checks(
            freshness_checks=freshness_checks, tags={"foo": "FOO"}
        )
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])

        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we should get a run request for never_eval and success_eval_expired.
        run_request = sensor(context)
        assert isinstance(run_request, dg.RunRequest)
        assert run_request.asset_check_keys == [
            dg.AssetCheckKey(dg.AssetKey("never_eval"), "freshness_check"),
            dg.AssetCheckKey(dg.AssetKey("success_eval_expired"), "freshness_check"),
        ]
        assert run_request.tags == {"foo": "FOO"}
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None


def test_sensor_evaluation_planned(instance: DagsterInstance) -> None:
    """Test the case where the asset check is currently planned to evaluate, and has never previously evaluated. We shouldn't be kicking off a new run of the check."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    # Check has never completed evaluation but is in flight. We should skip the check.
    frozen_time = get_current_datetime()
    with freeze_time(frozen_time):
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=make_new_run_id(),
                timestamp=time.time(),
                dagster_event=dg.DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=my_asset.key, check_name="freshness_check"
                    ),
                ),
            )
        )
        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])
        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we shouldn't get a run request for any asset checks.
        assert isinstance(sensor(context), dg.SkipReason)
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None


def test_sensor_eval_planned_prev_success(instance: DagsterInstance) -> None:
    """Test the case where the asset check is currently planned to evaluate, and has previously evaluated successfully. We should be kicking off a run of the check once the freshness interval has passed."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    # Check has never completed evaluation but is in flight. We should skip the check.
    frozen_time = get_current_datetime()
    with freeze_time(frozen_time - datetime.timedelta(minutes=5)):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset.key,
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: dg.FloatMetadataValue(frozen_time.timestamp() + 5)
                },
            )
        )
    with freeze_time(frozen_time):
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=make_new_run_id(),
                timestamp=time.time(),
                dagster_event=dg.DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=my_asset.key, check_name="freshness_check"
                    ),
                ),
            )
        )
        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])
        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we do not yet expect a run request, since the freshness interval has not yet passed.
        result = sensor(context)
        assert isinstance(result, dg.SkipReason)
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None

        # Move time forward to when the check should be evaluated.
        with freeze_time(frozen_time + datetime.timedelta(minutes=6)):
            # Upon evaluation, we should get a run request for the asset check.
            run_request = sensor(context)
            assert isinstance(run_request, dg.RunRequest)
            assert run_request.asset_check_keys == [
                dg.AssetCheckKey(my_asset.key, "freshness_check")
            ]
            # Cursor should be None, since we made it through all assets.
            assert context.cursor is None


def test_sensor_eval_planned_prev_failed(instance: DagsterInstance) -> None:
    """Test the case where the asset check is currently planned to evaluate, and has previously evaluated unsuccessfully. We should not be kicking off a run of the check."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    # Check has never completed evaluation but is in flight. We should skip the check.
    frozen_time = get_current_datetime()
    with freeze_time(frozen_time - datetime.timedelta(minutes=5)):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset.key,
                check_name="freshness_check",
                passed=False,
                metadata={},
            )
        )
    with freeze_time(frozen_time):
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=make_new_run_id(),
                timestamp=time.time(),
                dagster_event=dg.DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=my_asset.key, check_name="freshness_check"
                    ),
                ),
            )
        )
        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])
        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we should not get a run request for the asset check.
        result = sensor(context)
        assert isinstance(result, dg.SkipReason)
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None


def test_sensor_eval_failed_and_outdated(instance: DagsterInstance) -> None:
    """Test the case where the asset check has previously failed, but the result is now out of date. We should kick off a new check evaluation."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    frozen_time = get_current_datetime()
    with freeze_time(frozen_time - datetime.timedelta(minutes=5)):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset.key,
                check_name="freshness_check",
                passed=False,
                metadata={},
            )
        )
    # Freshness check has previously failed, but we've since received a materialization for the asset making it out of date.
    with freeze_time(frozen_time):
        instance.report_runless_asset_event(dg.AssetMaterialization(asset_key=my_asset.key))
        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])
        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we should get a run request for the asset check.
        run_request = sensor(context)
        assert isinstance(run_request, dg.RunRequest)
        assert run_request.asset_check_keys == [dg.AssetCheckKey(my_asset.key, "freshness_check")]
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None


def test_sensor_eval_planned_and_launched_by_sensor(instance: DagsterInstance) -> None:
    """Test the case where the asset check is currently planned to evaluate, but the sensor is what launched the in-flight evaluation. We should not kick off a new evaluation."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )
    sensor = dg.build_sensor_for_freshness_checks(
        freshness_checks=freshness_checks, name="my_sensor"
    )
    defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])

    frozen_time = get_current_datetime()
    with freeze_time(frozen_time - datetime.timedelta(minutes=5)):
        run_id = make_new_run_id()
        # Create a run, simulate started by this sensor
        create_run_for_test(
            instance=instance,
            run_id=run_id,
            job_name="my_sensor",
            tags={SENSOR_NAME_TAG: "my_sensor"},
        )
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run_id,
                timestamp=time.time(),
                dagster_event=dg.DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=my_asset.key, check_name="freshness_check"
                    ),
                ),
            )
        )

    with freeze_time(frozen_time):
        context = dg.build_sensor_context(instance=instance, definitions=defs)
        skip_reason = sensor(context)
        assert isinstance(skip_reason, dg.SkipReason)


def test_sensor_eval_success_and_outdated(instance: DagsterInstance) -> None:
    """Test the case where the asset check has previously succeeded, but the result is now out of date. We should not kick off an evaluation unless FRESH_UNTIL_TIMESTAMP has passed."""

    @dg.asset
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    frozen_time = get_current_datetime()
    with freeze_time(frozen_time - datetime.timedelta(minutes=5)):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset.key,
                check_name="freshness_check",
                passed=True,
                metadata={
                    FRESH_UNTIL_METADATA_KEY: dg.FloatMetadataValue(
                        (frozen_time + datetime.timedelta(minutes=5)).timestamp()
                    )
                },
            )
        )
    # Freshness check has previously succeeded, but we've since received a materialization for the asset making it out of date.
    with freeze_time(frozen_time):
        instance.report_runless_asset_event(dg.AssetMaterialization(asset_key=my_asset.key))
        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])
        context = dg.build_sensor_context(instance=instance, definitions=defs)

        # Upon evaluation, we should not get a run request for the asset check.
        skip_reason = sensor(context)
        assert isinstance(skip_reason, dg.SkipReason)
        # Cursor should be None, since we made it through all assets.
        assert context.cursor is None


def test_sensor_cursor_recovery(instance: DagsterInstance) -> None:
    """Test the case where we have a cursor to evaluate from."""

    @dg.multi_asset(
        outs={
            "a": dg.AssetOut(),
            "b": dg.AssetOut(),
            "c": dg.AssetOut(),
            "d": dg.AssetOut(),
        },
    )
    def my_asset():
        pass

    freshness_checks = dg.build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )

    frozen_time = get_current_datetime()
    out_of_date_metadata = {
        FRESH_UNTIL_METADATA_KEY: dg.FloatMetadataValue(
            (frozen_time - datetime.timedelta(minutes=5)).timestamp()
        )
    }
    with freeze_time(frozen_time):
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("a"),
                check_name="freshness_check",
                passed=True,
                metadata=out_of_date_metadata,
            )
        )
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("b"),
                check_name="freshness_check",
                passed=True,
                metadata=out_of_date_metadata,
            )
        )
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("c"),
                check_name="freshness_check",
                passed=True,
                metadata=out_of_date_metadata,
            )
        )
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=dg.AssetKey("d"),
                check_name="freshness_check",
                passed=True,
                metadata=out_of_date_metadata,
            )
        )

        sensor = dg.build_sensor_for_freshness_checks(freshness_checks=freshness_checks)
        defs = dg.Definitions(asset_checks=freshness_checks, assets=[my_asset], sensors=[sensor])

        # Since we're starting evaluation at the second asset, we should have started evaluation at the third asset.
        context = dg.build_sensor_context(
            instance=instance,
            definitions=defs,
            cursor=dg.AssetCheckKey(dg.AssetKey("b"), "freshness_check").to_user_string(),
        )

        # Upon evaluation, we should get a run request for .
        run_request = sensor(context)
        assert isinstance(run_request, dg.RunRequest)
        assert run_request.asset_check_keys == [
            dg.AssetCheckKey(dg.AssetKey("c"), "freshness_check"),
            dg.AssetCheckKey(dg.AssetKey("d"), "freshness_check"),
            dg.AssetCheckKey(dg.AssetKey("a"), "freshness_check"),
            dg.AssetCheckKey(dg.AssetKey("b"), "freshness_check"),
        ]
        # Cursor should be None, since we made it through all remaining assets.
        assert context.cursor is None
