from dataclasses import dataclass

from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.time_window_partitions import get_time_partitions_def

from .asset_condition import AssetCondition, AssetConditionResult


@dataclass(frozen=True)
class LatestPartitionsCondition(AssetCondition):
    """AssetCondition which is true for a given asset partition if it is the last partition key
    for the asset. For unpartitioned assets, this will always be true. For time-partitioned assets
    and multi-partitioned assets with a time window dimension, this will be true for all partitions
    in the latest time window. For all other partitions definitions, this will be true for the
    final partition of the asset.
    """

    @property
    def description(self) -> str:
        return "Is the latest asset partition for this asset"

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        time_partitions_def = get_time_partitions_def(context.partitions_def)

        if context.partitions_def is None:
            # unpartitioned, always true
            true_subset = AssetSubset.all(context.asset_key, None)
        elif (
            isinstance(context.partitions_def, MultiPartitionsDefinition)
            and time_partitions_def is not None
        ):
            # multi-partitioned with time dimension, true for all partitions in latest time window
            latest_time_partition_key = time_partitions_def.get_last_partition_key(
                current_time=context.evaluation_time,
                dynamic_partitions_store=context.instance_queryer,
            )
            true_subset = AssetSubset.from_asset_partitions_set(
                context.asset_key,
                context.partitions_def,
                {
                    AssetKeyPartitionKey(context.asset_key, partition_key)
                    for partition_key in context.partitions_def.get_multipartition_keys_with_dimension_value(
                        context.partitions_def.time_window_dimension.name,
                        latest_time_partition_key,
                        dynamic_partitions_store=context.instance_queryer,
                    )
                }
                if latest_time_partition_key is not None
                else set(),
            )
        else:
            # other, true for latest partition key
            latest_partition_key = context.partitions_def.get_last_partition_key(
                context.evaluation_time, context.instance_queryer
            )
            true_subset = AssetSubset.from_asset_partitions_set(
                context.asset_key,
                context.partitions_def,
                {AssetKeyPartitionKey(context.asset_key, latest_partition_key)}
                if latest_partition_key is not None
                else set(),
            )

        return AssetConditionResult.create(context, true_subset=true_subset)
