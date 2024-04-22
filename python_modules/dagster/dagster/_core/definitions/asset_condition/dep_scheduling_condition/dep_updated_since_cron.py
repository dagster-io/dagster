import datetime
from typing import Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)
from dagster._utils import utc_datetime_from_timestamp
from dagster._utils.schedules import cron_string_iterator, reverse_cron_string_iterator

from ..asset_condition_evaluation_context import AssetConditionEvaluationContext
from .dep_scheduling_condition import DepSchedulingCondition


class DepUpdatedSinceCronCondition(DepSchedulingCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def condition_description(self) -> str:
        return "updated since the latest cron schedule tick after this asset was last updated"

    def _get_canonical_datetime(
        self,
        context: AssetConditionEvaluationContext,
        candidate_asset_partition: AssetKeyPartitionKey,
    ) -> Optional[datetime.datetime]:
        if isinstance(context.partitions_def, TimeWindowPartitionsDefinition):
            return context.partitions_def.time_window_for_partition_key(
                partition_key=candidate_asset_partition.partition_key
            ).end
        else:
            latest_record = (
                context.instance_queryer.get_latest_materialization_or_observation_record(
                    candidate_asset_partition
                )
            )
            return utc_datetime_from_timestamp(latest_record.timestamp) if latest_record else None

    def _get_next_cron_tick(self, dt: datetime.datetime) -> datetime.datetime:
        next_ticks = cron_string_iterator(
            start_timestamp=dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(next_ticks)

    def _get_previous_cron_tick(self, dt: datetime.datetime) -> datetime.datetime:
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(previous_ticks)

    def get_base_cron_schedule_tick(
        self,
        context: AssetConditionEvaluationContext,
        candidate_asset_partition: AssetKeyPartitionKey,
    ) -> datetime.datetime:
        """Returns the tick of the cron schedule for which each dep asset partition should be
        materialized more recently than.
        """
        canonical_datetime = self._get_canonical_datetime(context, candidate_asset_partition)

        if canonical_datetime is None:
            # If this asset has never been materialized or observed, we just use the previous tick
            return self._get_previous_cron_tick(context.evaluation_time)
        else:
            # If this asset has been materialized or observed, then we use the tick after that time
            return self._get_next_cron_tick(canonical_datetime)

    def get_subset_to_evaluate(self, context: AssetConditionEvaluationContext) -> ValidAssetSubset:
        # whenever a new cron tick is passed, re-evaluate all candidates
        previous_cron_timestamp = self._get_previous_cron_tick(context.evaluation_time).timestamp()
        if previous_cron_timestamp > (context.previous_evaluation_timestamp or 0):
            return context.candidate_subset

        return super().get_subset_to_evaluate(context)

    def evaluate_for_dep_asset_partition(
        self,
        context: AssetConditionEvaluationContext,
        dep_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        if context.will_update_asset_partition(dep_asset_partition):
            return True

        dep_partitions_def = context.asset_graph.get(dep_asset_partition.asset_key).partitions_def
        if isinstance(dep_partitions_def, TimeWindowPartitionsDefinition):
            # if a time-partition exists, the asset is considered to be "up to date" for the slice
            # of time specified by that partition key
            return context.instance_queryer.asset_partition_has_materialization_or_observation(
                asset_partition=dep_asset_partition
            )
        else:
            # for other partition types, the materialization event must have occurred after the last
            # cron tick of the given schedule
            return (
                dep_asset_partition
                in context.instance_queryer.get_asset_subset_updated_after_time(
                    asset_key=dep_asset_partition.asset_key,
                    after_time=self._get_previous_cron_tick(context.evaluation_time),
                )
            )

    def evaluate_for_dep(
        self,
        context: AssetConditionEvaluationContext,
        dep: AssetKey,
        candidate_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        dep_partitions_def = context.asset_graph.get(dep).partitions_def
        if isinstance(dep_partitions_def, TimeWindowPartitionsDefinition):
            base_tick = self.get_base_cron_schedule_tick(context, candidate_asset_partition)
            # for TimeWindowPartitions, only look for updates to partitions since the last time the
            # base cron tick was evaluated
            selected_partition_keys = dep_partitions_def.get_partition_keys_in_time_window(
                TimeWindow(start=base_tick, end=context.evaluation_time)
            )
            return self.dep_partition_selection_type.method(
                self.evaluate_for_dep_asset_partition(
                    context, AssetKeyPartitionKey(dep, partition_key)
                )
                for partition_key in selected_partition_keys
            )
        else:
            return super().evaluate_for_dep(context, dep, candidate_asset_partition)
