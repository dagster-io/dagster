from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Sequence,
)

import pendulum

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetSubsetWithMetadata,
)
from dagster._serdes.serdes import PackableValue

from ..scheduling_condition import SchedulingCondition

if TYPE_CHECKING:
    from ..scheduling_context import SchedulingContext


class AssetCondition(SchedulingCondition):
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

    @staticmethod
    def parent_newer() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "SchedulingCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been updated
        since the latest tick of the given cron schedule. For partitioned assets with a time
        component, this can only be true for the most recent partition.
        """
        from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule

        from .rule_condition import RuleCondition

        return ~RuleCondition(rule=AutoMaterializeRule.materialize_on_cron(cron_schedule, timezone))

    @staticmethod
    def parents_updated_since_cron(
        cron_schedule: str, timezone: str = "UTC"
    ) -> "SchedulingCondition":
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


@dataclass(frozen=True)
class AssetConditionResult:
    condition: SchedulingCondition
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
