from dagster._core.definitions.events import AssetKeyPartitionKey

from ..asset_condition_evaluation_context import AssetConditionEvaluationContext
from .dep_scheduling_condition import DepSchedulingCondition


class DepMissingSchedulingCondition(DepSchedulingCondition):
    @property
    def condition_description(self) -> str:
        return "never been materialized or observed"

    def evaluate_for_dep_asset_partition(
        self,
        context: AssetConditionEvaluationContext,
        dep_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        return not (
            context.will_update_asset_partition(dep_asset_partition)
            or context.instance_queryer.asset_partition_has_materialization_or_observation(
                asset_partition=dep_asset_partition
            )
        )
