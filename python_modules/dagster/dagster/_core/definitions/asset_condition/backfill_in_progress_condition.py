from dataclasses import dataclass

from dagster._core.definitions.asset_condition.asset_condition import AssetConditionResult
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_condition import AssetCondition


@whitelist_for_serdes
@dataclass(frozen=True)
class BackfillInProgressCondition(AssetCondition):
    """Determines if an asset partition is part of an in-progress backfill.

    Args:
        any_partition (bool): If True, the condition will be true for all partitions of the asset
            if any partition of the asset is part of an in-progress backfill. If False, the
            condition will only be true for the partitions of the asset that are currently being
            backfilled. Defaults to False.
    """

    any_partition: bool = False

    @property
    def description(self) -> str:
        if self.any_partition:
            return "part of an asset targeted by an in-progress backfill"
        else:
            return "targeted by an in-progress backfill"

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        backfilling_subset = (
            # this backfilling subset is aware of the current partitions definitions, and so will
            # be valid
            (context.instance_queryer.get_active_backfill_target_asset_graph_subset())
            .get_asset_subset(context.asset_key, context.asset_graph)
            .as_valid(context.partitions_def)
        )

        if backfilling_subset.size == 0:
            true_subset = context.empty_subset()
        elif self.any_partition:
            true_subset = context.candidate_subset
        else:
            true_subset = context.candidate_subset & backfilling_subset

        return AssetConditionResult.create(context, true_subset)
