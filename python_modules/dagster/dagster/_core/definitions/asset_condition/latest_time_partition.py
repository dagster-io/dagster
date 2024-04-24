from .asset_condition import AssetCondition, AssetConditionResult
from .asset_condition_evaluation_context import AssetConditionEvaluationContext


class LatestTimePartitionCondition(AssetCondition):
    @property
    def description(self) -> str:
        return "Within the latest time partition of this asset."

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        latest_time_window_subset = context.asset_graph_view.create_latest_time_window_slice(
            context.asset_key
        ).convert_to_valid_asset_subset()

        return AssetConditionResult.create(
            context=context, true_subset=context.candidate_subset & latest_time_window_subset
        )
