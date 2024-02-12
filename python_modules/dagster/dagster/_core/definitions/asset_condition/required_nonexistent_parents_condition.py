from collections import defaultdict
from dataclasses import dataclass

from dagster._core.definitions.asset_condition.asset_condition import AssetConditionResult
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_condition import AssetCondition


@whitelist_for_serdes
@dataclass(frozen=True)
class RequiresNonexistentParentsCondition(AssetCondition):
    """Determines if an asset partition is downstream of one or more partitions which are required
    but do not yet exist.
    """

    @property
    def description(self) -> str:
        return "required parent partitions do not exist"

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        asset_partitions_by_evaluation_data = defaultdict(set)

        subset_to_evaluate = (
            context.candidates_not_evaluated_on_previous_tick_subset
            | context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            nonexistent_parent_partitions = context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                candidate.asset_key,
                candidate.partition_key,
            ).required_but_nonexistent_parents_partitions

            parents_with_nonexistent_partitions = sorted(
                {parent.asset_key for parent in nonexistent_parent_partitions}
            )
            if parents_with_nonexistent_partitions:
                metadata = frozenset(
                    (f"parent_{i+1}", parent)
                    for i, parent in enumerate(parents_with_nonexistent_partitions)
                )
                asset_partitions_by_evaluation_data[metadata].add(candidate)

        true_subset, subsets_with_metadata = context.add_evaluation_data_from_previous_tick(
            asset_partitions_by_evaluation_data, ignore_subset=subset_to_evaluate
        )
        return AssetConditionResult.create(context, true_subset, subsets_with_metadata)
