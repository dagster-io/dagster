from .asset_condition import AssetCondition, AssetConditionResult
from .asset_condition_evaluation_context import AssetConditionEvaluationContext


class InProgressRunCondition(AssetCondition):
    @property
    def description(self) -> str:
        return "Asset partition is targeted by an in-progress run."

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        in_progress_subset = context.asset_graph_view.compute_in_progress_slice(
            context.asset_key
        ).convert_to_valid_asset_subset()

        return AssetConditionResult.create(
            context=context, true_subset=context.candidate_subset & in_progress_subset
        )
