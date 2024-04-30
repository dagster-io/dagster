from .asset_condition import AssetCondition, AssetConditionResult
from .scheduling_condition_evaluation_context import SchedulingConditionEvaluationContext


class WillBeRequestedCondition(AssetCondition):
    @property
    def description(self) -> str:
        return "Will be requested during this evaluation"

    def _can_execute_together(self, context: SchedulingConditionEvaluationContext) -> bool:
        return context.legacy_context.materializable_in_same_run(
            child_key=context.root_asset_key, parent_key=context.asset_key
        )

    def evaluate(self, context: SchedulingConditionEvaluationContext) -> AssetConditionResult:
        evaluation_state = context.current_evaluation_state_by_key.get(context.asset_key)
        if evaluation_state is None:
            true_subset = context.asset_graph_view.create_empty_slice(
                context.asset_key
            ).convert_to_valid_asset_subset()
        else:
            # bad name here, but previous_evaluation is actually the evaluation from this tick
            true_subset = evaluation_state.previous_evaluation.true_subset.as_valid(
                context.partitions_def
            )

        return AssetConditionResult.create(context, true_subset)
