# pyright: reportPrivateImportUsage=false

import datetime
import json

import pytest
from dagster import asset
from dagster._check import CheckError
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    build_last_update_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.utils import (
    unique_id_from_asset_and_check_keys,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetChecksForAssetKeysSelection
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import JsonMetadataValue, TimestampMetadataValue
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import freeze_time
from dagster._time import create_datetime
from dagster._utils.security import non_secure_md5_hash_str
from dagster._vendored.dateutil.relativedelta import relativedelta

from dagster_tests.definitions_tests.freshness_checks_tests.conftest import (
    add_new_event,
    assert_check_result,
)


def test_params() -> None:
    @asset
    def my_asset():
        pass

    check = build_last_update_freshness_checks(
        assets=[my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )[0]
    assert (
        check.node_def.name
        == f"freshness_check_{non_secure_md5_hash_str(json.dumps([str(my_asset.key)]).encode())[:8]}"
    )
    check_specs = list(check.check_specs)
    assert len(check_specs) == 1

    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_asset.key
    assert next(iter(check_specs)).metadata == {
        "dagster/freshness_params": JsonMetadataValue(
            {
                "lower_bound_delta_seconds": 600,
                "timezone": "UTC",
            }
        )
    }

    @asset
    def other_asset():
        pass

    other_check = build_last_update_freshness_checks(
        assets=[other_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )[0]
    assert isinstance(other_check, AssetChecksDefinition)
    assert check.node_def.name != other_check.node_def.name

    check = build_last_update_freshness_checks(
        assets=[my_asset],
        deadline_cron="0 0 * * *",
        lower_bound_delta=datetime.timedelta(minutes=10),
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_specs)).metadata == {
        "dagster/freshness_params": JsonMetadataValue(
            {
                "lower_bound_delta_seconds": 600,
                "deadline_cron": "0 0 * * *",
                "timezone": "UTC",
            }
        )
    }

    check = build_last_update_freshness_checks(
        assets=[my_asset.key], lower_bound_delta=datetime.timedelta(minutes=10)
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_asset.key

    src_asset = SourceAsset("source_asset")
    check = build_last_update_freshness_checks(
        assets=[src_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == src_asset.key

    check = build_last_update_freshness_checks(
        assets=[my_asset, src_asset], lower_bound_delta=datetime.timedelta(minutes=10)
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert {check_key.asset_key for check_key in check.check_keys} == {my_asset.key, src_asset.key}

    with pytest.raises(Exception, match="Found duplicate assets"):
        build_last_update_freshness_checks(
            assets=[my_asset, my_asset], lower_bound_delta=datetime.timedelta(minutes=10)
        )

    with pytest.raises(CheckError, match="Invalid cron string."):
        build_last_update_freshness_checks(
            assets=[my_asset],
            deadline_cron="very invalid",
            lower_bound_delta=datetime.timedelta(minutes=10),
        )

    check = build_last_update_freshness_checks(
        assets=[my_asset],
        lower_bound_delta=datetime.timedelta(minutes=10),
        deadline_cron="0 0 * * *",
        timezone="UTC",
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert next(iter(check.check_keys)).asset_key == my_asset.key

    check_multiple_assets = build_last_update_freshness_checks(
        assets=[my_asset, other_asset],
        lower_bound_delta=datetime.timedelta(minutes=10),
    )[0]
    check_multiple_assets_switched_order = build_last_update_freshness_checks(
        assets=[other_asset, my_asset],
        lower_bound_delta=datetime.timedelta(minutes=10),
    )[0]
    assert check_multiple_assets.node_def.name == check_multiple_assets_switched_order.node_def.name
    unique_id = unique_id_from_asset_and_check_keys([my_asset.key, other_asset.key])
    unique_id_switched_order = unique_id_from_asset_and_check_keys([other_asset.key, my_asset.key])
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id}"
    assert check_multiple_assets.node_def.name == f"freshness_check_{unique_id_switched_order}"


@pytest.mark.parametrize(
    "use_materialization",
    [True, False],
    ids=["materialization", "observation"],
)
def test_different_event_types(use_materialization: bool, instance: DagsterInstance) -> None:
    """Test that the freshness check works with different event types."""

    @asset
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 1, 1, 0, 0)
    lower_bound_delta = datetime.timedelta(minutes=10)

    with freeze_time(
        start_time - datetime.timedelta(minutes=(lower_bound_delta.seconds // 60) - 1)
    ):
        add_new_event(instance, my_asset.key, is_materialization=use_materialization)
    with freeze_time(start_time):
        check = build_last_update_freshness_checks(
            assets=[my_asset],
            lower_bound_delta=lower_bound_delta,
        )[0]
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, True)


def test_materialization_and_observation(instance: DagsterInstance) -> None:
    """Test that freshness check works when latest event is an observation, but it has no last_updated_time."""

    @asset
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 1, 1, 0, 0)
    lower_bound_delta = datetime.timedelta(minutes=10)

    with freeze_time(
        start_time - datetime.timedelta(minutes=(lower_bound_delta.seconds // 60) - 1)
    ):
        # Add two events, one materialization and one observation. The observation event has no last_updated_time.
        add_new_event(instance, my_asset.key, is_materialization=True)
        add_new_event(instance, my_asset.key, is_materialization=False, include_metadata=False)

    with freeze_time(start_time):
        # Check data freshness, and expect it to pass.
        check = build_last_update_freshness_checks(
            assets=[my_asset],
            lower_bound_delta=lower_bound_delta,
        )[0]
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, True)


def test_observation_descriptions(instance: DagsterInstance) -> None:
    @asset
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 1, 1, 0, 0)
    lower_bound_delta = datetime.timedelta(minutes=10)

    check = build_last_update_freshness_checks(
        assets=[my_asset],
        lower_bound_delta=lower_bound_delta,
    )[0]
    # First, create an event that is outside of the allowed time window.
    with freeze_time(
        start_time - datetime.timedelta(seconds=int(lower_bound_delta.total_seconds() + 1))
    ):
        add_new_event(instance, my_asset.key, is_materialization=False)
    # Check fails, and the description should reflect that we don't know the current state of the asset.
    with freeze_time(start_time):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue for an update.",
        )

        # Create an observation event within the allotted time window, but with an out of date last update time. Description should change.
        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=(
                start_time - datetime.timedelta(seconds=int(lower_bound_delta.total_seconds() + 1))
            ).timestamp(),
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset is overdue for an update.",
        )

        # Create an observation event within the allotted time window, with an up to date last update time. Description should change.
        add_new_event(
            instance,
            my_asset.key,
            is_materialization=False,
            override_timestamp=(start_time - datetime.timedelta(minutes=9)).timestamp(),
        )
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh.",
        )


def test_check_result_cron(
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with a cron, and ensure that the check passes and fails as expected."""

    @asset
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 1, 1, 0, 0)
    deadline_cron = "0 0 * * *"  # Every day at midnight.
    timezone = "UTC"
    lower_bound_delta = datetime.timedelta(minutes=10)

    check = build_last_update_freshness_checks(
        assets=[my_asset],
        deadline_cron=deadline_cron,
        lower_bound_delta=lower_bound_delta,
        timezone=timezone,
    )[0]

    freeze_datetime = start_time
    with freeze_time(freeze_datetime):
        # With no events, check fails.
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset has never been observed/materialized.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "deadline_cron": deadline_cron,
                        "timezone": timezone,
                        "lower_bound_delta_seconds": lower_bound_delta.total_seconds(),
                    }
                ),
                "dagster/freshness_lower_bound_timestamp": TimestampMetadataValue(
                    value=(
                        create_datetime(2021, 1, 1, 0, 0, 0) - datetime.timedelta(minutes=10)
                    ).timestamp()
                ),
                "dagster/latest_cron_tick_timestamp": TimestampMetadataValue(
                    value=create_datetime(2021, 1, 1, 0, 0, 0).timestamp()
                ),
            },
        )

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = create_datetime(2021, 1, 1, 0, 0, 0) - datetime.timedelta(minutes=10)
    with freeze_time(lower_bound - datetime.timedelta(minutes=1)):
        add_new_event(instance, my_asset.key)
    with freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within cron-lower_bound_delta.
    with freeze_time(lower_bound + datetime.timedelta(minutes=1)):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "deadline_cron": deadline_cron,
                        "timezone": timezone,
                        "lower_bound_delta_seconds": lower_bound_delta.total_seconds(),
                    }
                ),
                "dagster/last_updated_timestamp": TimestampMetadataValue(
                    value=(lower_bound + datetime.timedelta(minutes=1)).timestamp()
                ),
                "dagster/latest_cron_tick_timestamp": TimestampMetadataValue(
                    value=create_datetime(2021, 1, 1, 0, 0, 0).timestamp()
                ),
                "dagster/freshness_lower_bound_timestamp": TimestampMetadataValue(
                    value=lower_bound.timestamp()
                ),
                "dagster/fresh_until_timestamp": TimestampMetadataValue(
                    value=create_datetime(2021, 1, 2, 0, 0, 0).timestamp()
                ),
            },
        )

    # Advance a full day. By now, we would expect a new event to have been added.
    # Since that is not the case, we expect the check to fail.
    freeze_datetime = freeze_datetime + relativedelta(days=1)
    with freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, False)

    # Again, go back in time, and add an event within the time window we're checking.
    with freeze_time(
        create_datetime(2021, 1, 2, 0, 0, 0)
        - datetime.timedelta(minutes=10)
        + datetime.timedelta(minutes=1)
    ):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, True)


def test_check_result_bound_only(
    instance: DagsterInstance,
) -> None:
    """Move time forward and backward, with a freshness check parameterized with only a
    lower_bound_delta, and ensure that the check passes and fails as expected.
    """

    @asset
    def my_asset():
        pass

    start_time = create_datetime(2021, 1, 1, 1, 0, 0)
    lower_bound_delta = datetime.timedelta(minutes=10)

    check = build_last_update_freshness_checks(
        assets=[my_asset],
        lower_bound_delta=lower_bound_delta,
    )[0]

    freeze_datetime = start_time
    with freeze_time(freeze_datetime):
        # With no events, check fails.
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            False,
            description_match="Asset has never been observed/materialized.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "lower_bound_delta_seconds": 600,
                        "timezone": "UTC",
                    }
                ),
                "dagster/freshness_lower_bound_timestamp": TimestampMetadataValue(
                    (start_time - datetime.timedelta(minutes=10)).timestamp()
                ),
            },
        )

    # Add an event outside of the allowed time window. Check fails.
    lower_bound = create_datetime(2021, 1, 1, 0, 50, 0)
    with freeze_time(lower_bound - datetime.timedelta(minutes=1)):
        add_new_event(instance, my_asset.key)
    with freeze_time(freeze_datetime):
        assert_check_result(my_asset, instance, [check], AssetCheckSeverity.WARN, False)

    # Go back in time and add an event within the allowed time window.
    update_time = lower_bound + datetime.timedelta(minutes=1)
    with freeze_time(update_time):
        add_new_event(instance, my_asset.key)
    # Now we expect the check to pass.
    with freeze_time(freeze_datetime):
        assert_check_result(
            my_asset,
            instance,
            [check],
            AssetCheckSeverity.WARN,
            True,
            description_match="Asset is currently fresh.",
            metadata_match={
                "dagster/freshness_params": JsonMetadataValue(
                    {
                        "lower_bound_delta_seconds": 600,
                        "timezone": "UTC",
                    }
                ),
                "dagster/fresh_until_timestamp": TimestampMetadataValue(
                    value=update_time.timestamp() + 600
                ),
                "dagster/last_updated_timestamp": TimestampMetadataValue(
                    value=update_time.timestamp()
                ),
                "dagster/freshness_lower_bound_timestamp": TimestampMetadataValue(
                    value=lower_bound.timestamp()
                ),
            },
        )


def test_subset_freshness_checks(instance: DagsterInstance):
    """Test the multi asset case, ensure that the freshness check can be subsetted to execute only
    on a subset of assets.
    """

    @asset
    def my_asset():
        pass

    @asset
    def my_other_asset():
        pass

    check = build_last_update_freshness_checks(
        assets=[my_asset, my_other_asset],
        lower_bound_delta=datetime.timedelta(minutes=10),
    )[0]
    single_check_job = define_asset_job(
        "the_job", selection=AssetChecksForAssetKeysSelection(selected_asset_keys=[my_asset.key])
    )
    defs = Definitions(
        assets=[my_asset, my_other_asset], asset_checks=[check], jobs=[single_check_job]
    )
    job_def = defs.get_job_def("the_job")
    result = job_def.execute_in_process(instance=instance)
    assert result.success
    # Only one asset check should have occurred, and it should be for `my_asset`.
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].asset_key == my_asset.key
    assert not result.get_asset_check_evaluations()[0].passed
