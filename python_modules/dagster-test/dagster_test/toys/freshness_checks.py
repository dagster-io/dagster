import math
import random
from datetime import timedelta

from dagster import (
    AssetExecutionContext,
    MetadataValue,
    ObserveResult,
    ScheduleDefinition,
    TimestampMetadataValue,
    _check as check,
    asset,
    build_last_update_freshness_checks,
    build_sensor_for_freshness_checks,
    define_asset_job,
    observable_source_asset,
)
from dagster._core.definitions.asset_selection import KeysAssetSelection
from dagster._time import get_current_datetime


@observable_source_asset(group_name="freshness_checks")
def unreliable_source_events():
    """An asset which has a .8 probability of being updated every minute.

    We expect an update every 3 minutes, and the asset could have arrived within the last 2 minutes.
    """
    return ObserveResult(
        metadata={"dagster/last_updated_timestamp": get_last_updated_timestamp_unreliable_source()}
    )


@asset(non_argument_deps={unreliable_source_events.key}, group_name="freshness_checks")
def derived_asset(context: AssetExecutionContext) -> None:
    """An asset that depends on the unreliable source.

    We also expect this asset to be updated every 4 minutes.
    """
    latest_observations = context.instance.fetch_observations(
        records_filter=unreliable_source_events.key, limit=1
    )
    latest_updated_timestamp = check.float_param(
        check.not_none(latest_observations.records[0].asset_observation)
        .metadata["dagster/last_updated_timestamp"]
        .value,
        "latest_updated_timestamp",
    )
    if latest_updated_timestamp < (get_current_datetime() - timedelta(minutes=4)).timestamp():
        raise Exception("source is stale, so I am going to fail :(")


source_checks = build_last_update_freshness_checks(
    assets=[unreliable_source_events],
    deadline_cron="*/3 * * * *",
    lower_bound_delta=timedelta(minutes=2),
)

derived_checks = build_last_update_freshness_checks(
    assets=[derived_asset],
    deadline_cron="*/4 * * * *",
    lower_bound_delta=timedelta(minutes=3),
)


raw_events_schedule = ScheduleDefinition(
    job=define_asset_job(
        "observe_raw_events",
        selection=KeysAssetSelection(selected_keys=[unreliable_source_events.key]),
    ),
    cron_schedule="*/3 * * * *",
)

derived_asset_schedule = ScheduleDefinition(
    job=define_asset_job(
        "derived_asset_job",
        selection=KeysAssetSelection(selected_keys=[derived_asset.key]),
    ),
    cron_schedule="*/3 * * * *",
)

freshness_sensor = build_sensor_for_freshness_checks(
    freshness_checks=derived_checks,
    minimum_interval_seconds=5,
)


def get_last_updated_timestamp_unreliable_source() -> TimestampMetadataValue:
    context = AssetExecutionContext.get()
    latest_observations = context.instance.fetch_observations(
        records_filter=context.asset_key, limit=1
    )

    if random.random() < 0.3 and len(latest_observations.records) > 1:
        return check.not_none(latest_observations.records[0].asset_observation).metadata[
            "dagster/last_updated_timestamp"
        ]  # type: ignore
    else:
        now = get_current_datetime()
        rounded_minute = max(math.floor((now.minute - 1) / 3) * 3, 0)
        return MetadataValue.timestamp(now.replace(minute=rounded_minute))


def get_freshness_defs_pile():
    """Return all the relevant definitions which must be splatted into the repo."""
    return [
        unreliable_source_events,
        source_checks,
        raw_events_schedule,
        derived_asset,
        derived_checks,
        derived_asset_schedule,
        freshness_sensor,
    ]
