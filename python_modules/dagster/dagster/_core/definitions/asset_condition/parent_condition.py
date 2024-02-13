from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import dagster._check as check
from dagster._core.definitions.asset_condition.asset_condition import AssetConditionResult
from dagster._core.definitions.asset_condition.asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
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


@whitelist_for_serdes
class ParentAssetConditionMode(Enum):
    ALL_PARENT_ASSETS: str
    ALL_PARENT_PARTITIONS: str
    ANY_PARENT_PARTITIONS: str


class ParentAssetCondition(AssetCondition):
    """Represents a condition that depends on some susbet of the parent asset having a given
    property.

    Args:
        mode (ParentConditionMode): The mode of the condition. If ALL_PARENT_ASSETS, the condition
            is true if at least one partition of each parent asset. If ANY_PARENT_PARTITIONS, the
            condition is true if any parent partition has the given property. If ALL_PARENT_PARTITIONS,
            the condition is true if all parent partitions have the given property.
    """

    mode: ParentAssetConditionMode

    def get_previous_parent_subset(
        self, context: AssetConditionEvaluationContext, parent_key: AssetKey
    ) -> Optional[ValidAssetSubset]:
        """Returns the subset of the parent asset that matched this condition on the previous
        evaluation. If no previous evaluation exists, returns an empty subset.
        """
        previous_parent_susbets = (
            context.previous_evaluation_state.get_extra_state(context.condition, list)
            if context.previous_evaluation_state
            else None
        ) or []
        return next(
            (s for s in previous_parent_susbets if s.asset_key == parent_key),
            context.empty_subset(),
        ).as_valid(context.partitions_def)

    @abstractmethod
    def get_current_parent_subset(
        self, context: AssetConditionEvaluationContext, parent_key: AssetKey
    ) -> ValidAssetSubset:
        ...

    def get_potential_parent_subset(
        self, context: AssetConditionEvaluationContext, parent_key: AssetKey
    ) -> ValidAssetSubset:
        return context.empty_subset()

    def get_subset_to_evaluate(self, context: AssetConditionEvaluationContext) -> ValidAssetSubset:
        return context.candidate_subset

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        current_parent_subsets = {
            parent_key: self.get_current_parent_subset(context, parent_key)
            for parent_key in context.asset_graph.get_parents(context.asset_key)
        }
        future_parent_subsets = {
            parent_key: self.get_potential_parent_subset(context, parent_key)
            for parent_key in context.asset_graph.get_parents(context.asset_key)
        }
        subset_to_evaluate = self.get_subset_to_evaluate(context)

        # exit early if nothing to evaluate
        if subset_to_evaluate.size == 0:
            return AssetConditionResult.create(
                context, context.empty_subset(), extra_state=list(current_parent_subsets.values())
            )

        # get the children whose parents have the given property, or will if executed on this tick
        child_subsets_by_parent_key = {}
        for parent_key in context.asset_graph.get_parents(context.asset_key):
            parent_subset = current_parent_subsets[parent_key] | future_parent_subsets[parent_key]
            child_subsets_by_parent_key[parent_key] = context.asset_graph.get_child_asset_subset(
                parent_subset, context.asset_key, context.instance_queryer, context.evaluation_time
            )

        if self.mode == ParentAssetConditionMode.ANY_PARENT_PARTITIONS:
            true_subset = context.empty_subset()
            # if any parent partition has the given property, the condition is true
            for child_subset in child_subsets_by_parent_key.values():
                true_subset |= child_subset
        elif self.mode == ParentAssetConditionMode.ALL_PARENT_ASSETS:
            true_subset = context.candidate_subset
            # if at least one partition of each parent has the given property, the condition is true
            for child_subset in child_subsets_by_parent_key.values():
                true_subset &= child_subset
        elif self.mode == ParentAssetConditionMode.ALL_PARENT_PARTITIONS:
            # must ensure that all parent partitions have the given property
            true_candidates = set()
            for candidate in subset_to_evaluate.asset_partitions:
                parent_partitions = context.asset_graph.get_parents_partitions(
                    context.instance_queryer,
                    context.evaluation_time,
                    candidate.asset_key,
                    candidate.partition_key,
                ).parent_partitions
                if all(
                    p in current_parent_subsets[parent_key]
                    or p in future_parent_subsets[parent_key]
                    for p in parent_partitions
                ):
                    true_candidates.add(candidate)
            true_subset = AssetSubset.from_asset_partitions_set(
                context.asset_key, context.partitions_def, true_candidates
            )

        else:
            check.failed(f"Unexpected mode {self.mode}")

        return AssetConditionResult.create(
            context, true_subset, extra_state=list(current_parent_subsets.values())
        )


class ParentNewerCondition(ParentAssetCondition):
    def get_subset_to_evaluate(self, context: AssetConditionEvaluationContext) -> ValidAssetSubset:
        return super().get_subset_to_evaluate(context)

    def get_current_parent_subset(
        self, context: AssetConditionEvaluationContext, asset_key: AssetKey
    ) -> ValidAssetSubset:
        previous_parent_subset = self.get_previous_parent_subset(context, asset_key)
        if previous_parent_subset is None:
            # previous data not valid, so rebuild from scratch
            return context.instance_queryer.get_asset_subset_updated_after_cursor(
                asset_key=context.asset_key,
                after_cursor=context.instance_queryer.get_latest_materialization_or_observation_storage_id(
                    AssetKeyPartitionKey(context.asset_key, None)
                )
                or 0,
            )
        else:
            # just fetch the subset updated since the previous tick
            newly_updated_parent_subset = (
                context.instance_queryer.get_asset_subset_updated_after_cursor(
                    asset_key=asset_key, after_cursor=context.previous_max_storage_id
                )
            )
            return newly_updated_parent_subset | previous_parent_subset

    def get_potential_parent_subset(
        self, context: AssetConditionEvaluationContext, parent_key: AssetKey
    ) -> ValidAssetSubset:
        return context.get_will_update_with_asset_subset(parent_key)

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        return AssetConditionResult.create(context, context.candidate_subset)
