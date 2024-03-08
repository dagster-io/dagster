import datetime
from typing import (
    AbstractSet,
    NamedTuple,
    Optional,
    Sequence,
)

from dagster import _check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionsDefinition,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    get_time_partitions_def,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._utils.schedules import (
    cron_string_iterator,
    reverse_cron_string_iterator,
)


class MissedTicksEvaluationData(NamedTuple):
    cron_schedule: str
    cron_timezone: str
    start_dt: Optional[datetime.datetime]
    end_dt: datetime.datetime

    @property
    def start_timestamp(self) -> Optional[float]:
        return self.start_dt.timestamp() if self.start_dt else None

    @property
    def end_timestamp(self) -> float:
        return self.end_dt.timestamp()


def last_tick_in_cron_schedule(
    missed_ticks_data: MissedTicksEvaluationData,
) -> Sequence[datetime.datetime]:
    last_tick_dt = next(
        reverse_cron_string_iterator(
            end_timestamp=missed_ticks_data.end_timestamp,
            cron_string=missed_ticks_data.cron_schedule,
            execution_timezone=missed_ticks_data.cron_timezone,
        )
    )
    return [last_tick_dt]


def cron_ticks_in_time_range(
    missed_ticks_data: MissedTicksEvaluationData,
) -> Sequence[datetime.datetime]:
    start_ts = check.not_none(missed_ticks_data.start_timestamp, "start_timestamp must be set")
    missed_ticks = []
    for dt in cron_string_iterator(
        start_timestamp=start_ts,
        cron_string=missed_ticks_data.cron_schedule,
        execution_timezone=missed_ticks_data.cron_timezone,
    ):
        if dt.timestamp() > missed_ticks_data.end_timestamp:
            break
        missed_ticks.append(dt)
    return missed_ticks


def get_missed_ticks(missed_ticks_data: MissedTicksEvaluationData) -> Sequence[datetime.datetime]:
    """Return the cron ticks between start and end. If end is None, return the last tick."""
    return (
        cron_ticks_in_time_range(missed_ticks_data)
        if missed_ticks_data.start_timestamp
        else last_tick_in_cron_schedule(missed_ticks_data)
    )


def get_new_asset_partitions_to_request(
    *,
    missed_ticks: Sequence[datetime.datetime],
    asset_key: AssetKey,
    partitions_def: Optional[PartitionsDefinition],
    dynamic_partitions_store: DynamicPartitionsStore,
    all_partitions: bool,
    end_dt: datetime.datetime,
) -> AbstractSet[AssetKeyPartitionKey]:
    if partitions_def is None:
        return {AssetKeyPartitionKey(asset_key)}

    # if all_partitions is set, then just return all partitions if any ticks have been missed
    if all_partitions:
        return {
            AssetKeyPartitionKey(asset_key, partition_key)
            for partition_key in partitions_def.get_partition_keys(
                current_time=end_dt,
                dynamic_partitions_store=dynamic_partitions_store,
            )
        }

    # for partitions_defs without a time component, just return the last partition if any ticks
    # have been missed
    time_partitions_def = get_time_partitions_def(partitions_def)
    if time_partitions_def is None:
        return {
            AssetKeyPartitionKey(
                asset_key,
                partitions_def.get_last_partition_key(
                    dynamic_partitions_store=dynamic_partitions_store
                ),
            )
        }

    missed_time_partition_keys = filter(
        None,
        [
            time_partitions_def.get_last_partition_key(
                current_time=missed_tick,
                dynamic_partitions_store=dynamic_partitions_store,
            )
            for missed_tick in missed_ticks
        ],
    )
    # for multi partitions definitions, request to materialize all partitions for each missed
    # cron schedule tick
    if isinstance(partitions_def, MultiPartitionsDefinition):
        return {
            AssetKeyPartitionKey(asset_key, partition_key)
            for time_partition_key in missed_time_partition_keys
            for partition_key in partitions_def.get_multipartition_keys_with_dimension_value(
                partitions_def.time_window_dimension.name,
                time_partition_key,
                dynamic_partitions_store=dynamic_partitions_store,
            )
        }
    else:
        return {
            AssetKeyPartitionKey(asset_key, time_partition_key)
            for time_partition_key in missed_time_partition_keys
        }
