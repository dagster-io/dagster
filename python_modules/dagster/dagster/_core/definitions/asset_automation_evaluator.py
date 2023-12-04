from abc import ABC, abstractmethod
from typing import List, Mapping, NamedTuple, Optional, Sequence, Set

from dagster import MetadataValue
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonAssetCursor
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.metadata import MetadataMapping

from .asset_automation_condition_context import AssetAutomationConditionEvaluationContext
from .asset_automation_condition_cursor import (
    AssetAutomationConditionCursor,
)
from .asset_subset import AssetSubset


class AssetAutomationConditionSnapshot(NamedTuple):
    """A serializable snapshot of an AssetAutomationCondition."""

    class_name: str
    description: Optional[str]


class AssetSubsetWithMetadata(NamedTuple):
    asset_subset: AssetSubset
    metadata: Mapping[str, MetadataValue]


class ConditionEvaluation(NamedTuple):
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition_snapshot: "AssetAutomationConditionSnapshot"
    true_subset: AssetSubset
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]
    child_evaluations: Sequence["ConditionEvaluation"]

    def for_child(self, child_condition: "AutomationCondition") -> Optional["ConditionEvaluation"]:
        for child_evaluation in self.child_evaluations:
            if child_evaluation.condition_snapshot == child_condition.to_snapshot():
                return child_evaluation
        return None

    def is_equivalent(self, other: Optional["ConditionEvaluation"]) -> bool:
        return (
            other is not None
            and self.condition_snapshot == other.condition_snapshot
            and self.true_subset == other.true_subset
            and self.candidate_subset == other.candidate_subset
            and len(self.child_evaluations) == len(other.child_evaluations)
            and all(
                self.child_evaluations[i].is_equivalent(other.child_evaluations[i])
                for i in range(len(self.child_evaluations))
            )
        )


class ConditionEvaluationResult(NamedTuple):
    asset_key: AssetKey
    evaluation: ConditionEvaluation
    cursor: AssetAutomationConditionCursor

    @property
    def true_subset(self) -> AssetSubset:
        return self.evaluation.true_subset

    @staticmethod
    def create(
        context: AssetAutomationConditionEvaluationContext,
        true_subset: AssetSubset,
        asset_subsets_with_metadata: Optional[Sequence[AssetSubsetWithMetadata]] = None,
        cursor: Optional[AssetAutomationConditionCursor] = None,
        child_results: Optional[Sequence["ConditionEvaluationResult"]] = None,
    ) -> "ConditionEvaluationResult":
        condition_snapshot = context.condition.to_snapshot()
        return ConditionEvaluationResult(
            asset_key=context.asset_key,
            evaluation=ConditionEvaluation(
                condition_snapshot=condition_snapshot,
                true_subset=true_subset,
                subsets_with_metadata=asset_subsets_with_metadata or [],
                candidate_subset=context.candidates_subset,
                child_evaluations=[result.evaluation for result in child_results or []],
            ),
            cursor=cursor
            or AssetAutomationConditionCursor(
                condition_snapshot=condition_snapshot,
                child_cursors=[result.cursor for result in child_results or []],
                max_storage_id=None,  # TODO
            ),
        )

    def to_asset_cursor(self) -> AssetDaemonAssetCursor:
        return AssetDaemonAssetCursor(
            asset_key=self.asset_key,
            latest_evaluation=self.evaluation,
            condition_cursor=self.cursor,
        )


class AutomationCondition(ABC):
    @property
    def children(self) -> Sequence["AutomationCondition"]:
        return []

    @property
    def description(self) -> Optional[str]:
        return None

    @abstractmethod
    def evaluate(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        ...

    def to_snapshot(self) -> AssetAutomationConditionSnapshot:
        return AssetAutomationConditionSnapshot(
            class_name=self.__class__.__name__, description=self.description
        )

    def __and__(self, other: "AutomationCondition") -> "AutomationCondition":
        # group AndAutomationConditions together
        if isinstance(self, AndAutomationCondition):
            return AndAutomationCondition(children=[*self.children, other])
        return AndAutomationCondition(children=[self, other])

    def __or__(self, other: "AutomationCondition") -> "AutomationCondition":
        # group OrAutomationConditions together
        if isinstance(self, OrAutomationCondition):
            return OrAutomationCondition(children=[*self.children, other])
        return OrAutomationCondition(children=[self, other])

    def __invert__(self) -> "AutomationCondition":
        if isinstance(self, OrAutomationCondition):
            return NorAutomationCondition(children=self.children)
        return NorAutomationCondition(children=[self])


class AndAutomationCondition(
    AutomationCondition,
    NamedTuple("_AndAutomationCondition", [("children", Sequence[AutomationCondition])]),
):
    def evaluate(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        child_results = []
        true_subset = context.candidates_subset
        for child_condition in self.children:
            child_context = context.for_child(
                condition=child_condition, candidates_subset=true_subset
            )
            child_result = child_condition.evaluate(child_context)
            child_results.append(child_result)
            true_subset &= child_result.true_subset
        return ConditionEvaluationResult.create(context, true_subset, child_results=child_results)


class OrAutomationCondition(
    AutomationCondition,
    NamedTuple("_OrAutomationCondition", [("children", Sequence[AutomationCondition])]),
):
    def evaluate(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        child_results: List[ConditionEvaluationResult] = []
        true_subset = context.asset_context.empty_subset()
        for child_condition in self.children:
            child_context = context.for_child(
                condition=child_condition, candidates_subset=context.candidates_subset
            )
            child_result = child_condition.evaluate(child_context)
            child_results.append(child_result)
            true_subset |= child_result.true_subset
        return ConditionEvaluationResult.create(context, true_subset, child_results=child_results)


class NorAutomationCondition(
    AutomationCondition,
    NamedTuple("_NorAutomationCondition", [("children", Sequence[AutomationCondition])]),
):
    def evaluate(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        child_results: List[ConditionEvaluationResult] = []
        true_subset = context.candidates_subset
        for child_condition in self.children:
            child_context = context.for_child(
                condition=child_condition, candidates_subset=context.candidates_subset
            )
            child_result = child_condition.evaluate(child_context)
            child_results.append(child_result)
            true_subset -= child_result.true_subset
        return ConditionEvaluationResult.create(context, true_subset, child_results=child_results)


############
# NOT BOOLEAN STUFF
############


class IsMissingCondition(AutomationCondition, NamedTuple("_IsMissingCondition", [])):
    @property
    def description(self) -> str:
        return "materialization is missing"

    def evaluate_for_asset(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        previous_handled_subset = (
            context.get_cursor_extra("previous_handled_subset", astype=AssetSubset)
            or context.empty_subset()
        )

        current_handled_subset = (
            previous_handled_subset
            | context.materialized_since_previous_tick_subset
            | context.asset_context.previous_tick_requested_subset
        )
        current_unhandled_subset = context.candidates_subset - current_handled_subset
        return ConditionEvaluationResult.create(
            context,
            true_subset=current_unhandled_subset,
            cursor=AssetAutomationConditionCursor(
                condition_snapshot=self.to_snapshot(),
                child_cursors=[],
                max_storage_id=None,  # TODO
                extras={
                    "previous_handled_subset": current_handled_subset,
                },
            ),
        )


class ParentOutdatedCondition(AutomationCondition, NamedTuple("_ParentOutdatedCondition", [])):
    @property
    def description(self) -> str:
        return "waiting on upstream data to be up to date"

    def outdated_ancestors(
        self,
        context: AssetAutomationConditionEvaluationContext,
        asset_partition: AssetKeyPartitionKey,
    ) -> Set[AssetKey]:
        outdated_ancestors = set()
        for (
            parent
        ) in context.asset_context.get_parents_that_will_not_be_materialized_on_current_tick(
            asset_partition=asset_partition
        ):
            if context.instance_queryer.have_ignorable_partition_mapping_for_outdated(
                asset_partition.asset_key, parent.asset_key
            ):
                continue
            outdated_ancestors.update(
                context.instance_queryer.get_outdated_ancestors(asset_partition=parent)
            )
        return outdated_ancestors

    def evaluate_for_asset(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.candidates_not_evaluated_on_previous_tick_subset
            | context.candidate_parent_has_or_will_update_subset
        )

        asset_partitions_by_metadata: Mapping[MetadataMapping, Set[AssetKeyPartitionKey]] = {}
        for candidate in subset_to_evaluate.asset_partitions:
            outdated_ancestors = self.outdated_ancestors(context, candidate)
            # find the root cause of why this asset partition's parents are outdated (if any)
            if outdated_ancestors:
                metadata = {
                    f"outdated_ancestor_{i}": MetadataValue.asset(ak)
                    for i, ak in enumerate(sorted(outdated_ancestors))
                }
                asset_partitions_by_metadata[metadata].add(candidate)

        new_subsets_with_metadata = [
            AssetSubsetWithMetadata(
                asset_subset=AssetSubset.from_asset_partitions_set(
                    context.asset_key, context.partitions_def, asset_partitions
                ),
                metadata=metadata,
            )
            for metadata, asset_partitions in asset_partitions_by_metadata.items()
        ]
        true_subset = context.previous_tick_true_subset - subset_to_evaluate
        for subset_with_metadata in new_subsets_with_metadata:
            true_subset |= subset_with_metadata.asset_subset

        return ConditionEvaluationResult.create(
            context,
            true_subset,
            context.combine_previous_data(new_subsets_with_metadata, subset_to_evaluate),
        )


class BackfillInProgressCondition(
    AutomationCondition,
    NamedTuple("_BackfillInProgressCondition", [("all_partitions", bool)]),
):
    @property
    def description(self) -> str:
        if self.all_partitions:
            return "part of an asset targeted by an in-progress backfill"
        else:
            return "targeted by an in-progress backfill"

    def evaluate_for_asset(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        backfilling_subset = (
            context.instance_queryer.get_active_backfill_target_asset_graph_subset()
        ).get_asset_subset(context.asset_key, context.asset_context.asset_graph)

        if backfilling_subset.size == 0:
            true_subset = context.empty_subset()
        elif self.all_partitions:
            true_subset = context.candidates_subset
        else:
            true_subset = context.candidates_subset & backfilling_subset

        return ConditionEvaluationResult.create(context, true_subset=true_subset)


class ParentMissingCondition(AutomationCondition, NamedTuple("_ParentMissingCondition", [])):
    @property
    def description(self) -> str:
        return "waiting on upstream data to be present"

    def evaluate_for_asset(
        self, context: AssetAutomationConditionEvaluationContext
    ) -> ConditionEvaluationResult:
        subset_to_evaluate = (
            context.candidates_not_evaluated_on_previous_tick_subset
            | context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            missing_parent_asset_keys = set()
            for (
                parent
            ) in context.asset_context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                # ignore non-observable sources, which will never have a materialization or observation
                if context.asset_context.asset_graph.is_source(
                    parent.asset_key
                ) and not context.asset_context.asset_graph.is_observable(parent.asset_key):
                    continue
                if not context.instance_queryer.asset_partition_has_materialization_or_observation(
                    parent
                ):
                    missing_parent_asset_keys.add(parent.asset_key)
            if missing_parent_asset_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(missing_parent_asset_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in subset_to_evaluate,
        )
