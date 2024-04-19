from abc import abstractmethod
from enum import Enum
from typing import Any, Callable, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey

from ..asset_condition import AssetCondition, AssetConditionResult
from ..asset_condition_evaluation_context import AssetConditionEvaluationContext


class _SchedulingCondition(AssetCondition): ...


class DepSelectionType(Enum):
    ALL = "ALL"
    ANY = "ANY"

    @property
    def method(self) -> Callable[[Any], bool]:
        """Method to be used for aggregating results across a dep."""
        if self == DepSelectionType.ALL:
            return all
        else:
            return any


class DepSchedulingCondition(_SchedulingCondition):
    """DepSchedulingCondition is a base class for conditions which examine the state of the given
    asset's dependencies. At minimum, the subclass must implement `evaluate_for_dep_asset_partition`.

    This class caches the results of all evaluations between ticks. By default, an asset partition
    will be re-evaluated whenever a dependency is updated, or will update on a given tick. At this
    point in time, all of the dependencies will be re-evaluated. This is technically somewhat
    inefficient, but significantly simpler to implement.
    """

    dep_keys: Optional[Sequence[AssetKey]] = None
    dep_selection_type: DepSelectionType = DepSelectionType.ANY
    dep_partition_selection_type: DepSelectionType = DepSelectionType.ANY

    def select_dep_keys(self, dep_keys: Sequence[AssetKey]) -> "DepSchedulingCondition":
        return self.copy(update={"dep_keys": dep_keys})

    def all_deps(self) -> "DepSchedulingCondition":
        return self.copy(update={"dep_selection_type": DepSelectionType.ALL})

    def all_dep_partitions(self) -> "DepSchedulingCondition":
        return self.copy(update={"dep_partition_selection_type": DepSelectionType.ALL})

    @property
    def description(self) -> str:
        if self.dep_partition_selection_type == DepSelectionType.ALL:
            dep_partitions_str = "All partitions "
            has_or_have = "have"
        else:
            dep_partitions_str = "Any partition "
            has_or_have = "has"

        if self.dep_selection_type == DepSelectionType.ALL:
            dep_str = "all dependencies"
        else:
            dep_str = "any dependency"

        if self.dep_keys is not None:
            dep_str += f" within ({', '.join(k.to_user_string() for k in self.dep_keys)})"

        return f"{dep_partitions_str} of {dep_str} {has_or_have} {self.condition_description}"

    @property
    @abstractmethod
    def condition_description(self) -> str:
        """Description of the condition that will be evaluated for each dependency."""
        raise NotImplementedError()

    @abstractmethod
    def evaluate_for_dep_asset_partition(
        self,
        context: AssetConditionEvaluationContext,
        dep_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        """This method should be implemented to evaluate if the given dep asset partition satisfies
        the condition.
        """
        raise NotImplementedError()

    def evaluate_for_dep(
        self,
        context: AssetConditionEvaluationContext,
        dep: AssetKey,
        candidate_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        """For a given dep of a parent asset, evaluate if this rule is satisfied."""
        dep_asset_partitions = context.asset_graph.get_parent_asset_subset(
            child_asset_subset=AssetSubset.from_asset_partitions_set(
                context.asset_key, context.partitions_def, {candidate_asset_partition}
            ),
            parent_asset_key=dep,
            dynamic_partitions_store=context.instance_queryer,
            current_time=context.evaluation_time,
        ).asset_partitions

        return self.dep_partition_selection_type.method(
            self.evaluate_for_dep_asset_partition(context, dap) for dap in dep_asset_partitions
        )

    def evaluate_for_candidate(
        self,
        context: AssetConditionEvaluationContext,
        candidate_asset_partition: AssetKeyPartitionKey,
    ) -> bool:
        """Returns if the condition is satisfied for the given candidate asset partition."""
        return self.dep_selection_type.method(
            self.evaluate_for_dep(context, dep, candidate_asset_partition)
            for dep in self.get_dep_keys(context)
        )

    def get_subset_to_evaluate(self, context: AssetConditionEvaluationContext) -> ValidAssetSubset:
        """Typically, we only need to evaluate the net-new candidates and candidates whose parents
        have updated since the previous tick.
        """
        return (
            context.candidates_not_evaluated_on_previous_tick_subset
            | context.candidate_parent_has_or_will_update_subset
        )

    def get_dep_keys(self, context: AssetConditionEvaluationContext) -> Sequence[AssetKey]:
        """Returns the set of dependency keys that must be evaluated."""
        parent_keys = context.asset_graph.get(context.asset_key).parent_keys
        if self.dep_keys is None:
            return parent_keys
        else:
            return list(set(self.dep_keys) - set(parent_keys))

    def evaluate(self, context: AssetConditionEvaluationContext) -> "AssetConditionResult":
        to_evaluate_subset = self.get_subset_to_evaluate(context)
        new_true_subset = AssetSubset.from_asset_partitions_set(
            context.asset_key,
            context.partitions_def,
            {
                candidate
                for candidate in to_evaluate_subset.asset_partitions
                if self.evaluate_for_candidate(context, candidate)
            },
        )
        true_subset = (
            context.previous_true_subset.as_valid(context.partitions_def) - to_evaluate_subset
        ) | new_true_subset

        return AssetConditionResult.create(context, true_subset)
