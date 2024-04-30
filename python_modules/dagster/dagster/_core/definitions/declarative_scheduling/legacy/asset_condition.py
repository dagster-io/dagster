import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
    Sequence,
)

import pendulum

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
)
from dagster._model import DagsterModel
from dagster._serdes.serdes import PackableValue
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from ..scheduling_context import SchedulingContext


class AssetCondition(ABC, DagsterModel):
    """An AssetCondition represents some state of the world that can influence if an asset
    partition should be materialized or not. AssetConditions can be combined to create
    new conditions using the `&` (and), `|` (or), and `~` (not) operators.

    Examples:
        .. code-block:: python

            from dagster import AssetCondition, AutoMaterializePolicy

            # At least one parent is newer and no parent is missing.
            my_policy = AutoMaterializePolicy(
                asset_condition = AssetCondition.parent_newer() & ~AssetCondition.parent_missing()
            )
    """

    def get_unique_id(self, parent_unique_id: Optional[str]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @abstractmethod
    def evaluate(self, context: "SchedulingContext") -> "AssetConditionResult":
        raise NotImplementedError()

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def __and__(self, other: "AssetCondition") -> "AssetCondition":
        from ..operators.boolean_operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "AssetCondition") -> "AssetCondition":
        from ..operators.boolean_operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "AssetCondition":
        from ..operators.boolean_operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    @property
    def children(self) -> Sequence["AssetCondition"]:
        return []

    def get_snapshot(self, unique_id: str) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
        )

    @staticmethod
    def parent_newer() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been updated
        since the latest tick of the given cron schedule. For partitioned assets with a time
        component, this can only be true for the most recent partition.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return ~RuleCondition(rule=AutoMaterializeRule.materialize_on_cron(cron_schedule, timezone))

    @staticmethod
    def parents_updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when all parent asset
        partitions have been updated more recently than the latest tick of the given cron schedule.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return ~RuleCondition(
            rule=AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron(
                cron_schedule, timezone
            )
        )

    @staticmethod
    def any_deps_match(condition: "AssetCondition") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.
        """
        from ..operators.dep_operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @staticmethod
    def all_deps_match(condition: "AssetCondition") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.
        """
        from ..operators.dep_operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @staticmethod
    def missing_() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been materialized."""
        from ..operands.slice_conditions import MissingSchedulingCondition

        return MissingSchedulingCondition()

    @staticmethod
    def in_progress() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if it is part of an in-progress run."""
        from ..operands.slice_conditions import InProgressSchedulingCondition

        return InProgressSchedulingCondition()

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if you provide a delta of 48 hours for a daily-partitioned asset, this
                will return the last two partitions.
        """
        from ..operands.slice_conditions import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition(
            lookback_seconds=lookback_delta.total_seconds() if lookback_delta else None
        )


@dataclass(frozen=True)
class AssetConditionResult:
    condition: AssetCondition
    condition_unique_id: str
    start_timestamp: float
    end_timestamp: float

    true_slice: AssetSlice
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    extra_state: PackableValue
    child_results: Sequence["AssetConditionResult"]

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

    @staticmethod
    def create_from_children(
        context: "SchedulingContext",
        true_subset: ValidAssetSubset,
        child_results: Sequence["AssetConditionResult"],
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return AssetConditionResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=context.asset_graph_view.get_asset_slice_from_subset(true_subset),
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
        )

    @staticmethod
    def create(
        context: "SchedulingContext",
        true_subset: ValidAssetSubset,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: PackableValue = None,
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return AssetConditionResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=context.asset_graph_view.get_asset_slice_from_subset(true_subset),
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=subsets_with_metadata,
            child_results=[],
            extra_state=extra_state,
        )
