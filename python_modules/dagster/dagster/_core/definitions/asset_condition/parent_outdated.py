from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set

from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.metadata import MetadataValue

from .asset_condition import AssetCondition, AssetConditionResult
from .asset_condition_evaluation_context import NewAssetConditionEvaluationContext


@dataclass(frozen=True)
class ParentOutdatedAssetCondition(AssetCondition):
    """This serves as a sample implementation of the ParentOutdatedAssetCondition using the new
    AssetSlice APIs and a simplified context object.

    Note that we may want to avoid implementing ParentOutdated as a core condition, and instead use
    AncestorUnsynced or something of the sort.
    """

    @property
    def description(self) -> str:
        return ""

    def evaluate(self, context: NewAssetConditionEvaluationContext) -> "AssetConditionResult":
        slice_to_evaluate = (
            # evaluate any candidate partitions that have parents which have been updated since
            # the previous tick
            context.candidate_slice & context.compute_parent_updated_since_previous_tick_slice()
        ) | (
            # also evaluate any candidate partitions which were not evaluated in the previous tick
            context.candidate_slice - context.previous_candidate_subset
        )

        outdated_parents_by_asset_partition_key: Dict[AssetKeyPartitionKey, Set[AssetKey]] = (
            defaultdict(set)
        )
        for parent_asset_key in slice_to_evaluate.parent_keys:
            parent_slice = slice_to_evaluate.compute_parent_slice(parent_asset_key)
            outdated_parent_slice = parent_slice.compute_outdated_slice()
            child_of_outdated_slice = outdated_parent_slice.compute_child_slice(context.asset_key)
            for asset_partition_key in child_of_outdated_slice.compute_asset_partition_keys():
                outdated_parents_by_asset_partition_key[asset_partition_key].add(parent_asset_key)

        return AssetConditionResult.create_from_previous_evaluation(
            context,
            new_evaluated_slice=slice_to_evaluate,
            new_true_slice=context.asset_graph_view.get_asset_slice_from_asset_partition_keys(
                context.asset_key,
                {
                    apk
                    for apk, outdated_ancestors in outdated_parents_by_asset_partition_key.items()
                    if outdated_ancestors
                },
            ),
            new_metadata_by_asset_partition_key={
                asset_partition: {
                    f"waiting_on_parent_{i+1}": MetadataValue.asset(k)
                    for i, k in enumerate(sorted(outdated_ancestors))
                }
                for asset_partition, outdated_ancestors in outdated_parents_by_asset_partition_key.items()
                if outdated_ancestors
            },
        )
