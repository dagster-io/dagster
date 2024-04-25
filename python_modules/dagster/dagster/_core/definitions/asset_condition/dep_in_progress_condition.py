from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._utils.cached_method import cached_method

from .asset_condition_evaluation_context import AssetConditionEvaluationContext
from .dep_condition import DepSchedulingCondition


class DepInProgressCondition(DepSchedulingCondition):
    def dep_description(self) -> str:
        return "in progress"

    @cached_method
    def get_computed_in_progress_slice(
        self, *, asset_graph_view: AssetGraphView, dep: AssetKey
    ) -> AssetSlice:
        # caching layer to avoid recomputing the in-progress slice multiple times
        return asset_graph_view.compute_in_progress_slice(dep)

    def evaluate_for_dep_asset_partition(
        self, context: AssetConditionEvaluationContext, dep_asset_partition: AssetKeyPartitionKey
    ) -> bool:
        dep_in_progress_slice = self.get_computed_in_progress_slice(
            asset_graph_view=context.asset_graph_view, dep=dep_asset_partition.asset_key
        )
        return dep_in_progress_slice.contains_asset_partition(dep_asset_partition)
