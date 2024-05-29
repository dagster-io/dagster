import datetime
import logging
from typing import TYPE_CHECKING, AbstractSet, Any, Mapping, NamedTuple, Optional

import pendulum

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.declarative_scheduling.legacy.asset_condition import AssetCondition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    SchedulingEvaluationInfo,
)
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    HistoricalAllPartitionsSubsetSentinel,
    SchedulingConditionCursor,
    SchedulingConditionNodeCursor,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition

from .legacy.legacy_context import LegacyRuleEvaluationContext

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


def _has_legacy_condition(condition: SchedulingCondition):
    """Detects if the given condition has any legacy rules."""
    if isinstance(condition, AssetCondition):
        return True
    else:
        return any(_has_legacy_condition(child) for child in condition.children)


# This class exists purely for organizational purposes so that we understand
# the interface between scheduling conditions and the instance much more
# explicitly. This captures all interactions that do not go through AssetGraphView
# so that we do not access the legacy context or the instance queryer directly
# in scheduling conditions.
class NonAGVInstanceInterface:
    def __init__(self, queryer: "CachingInstanceQueryer"):
        self._queryer = queryer

    def get_asset_subset_updated_after_time(
        self, *, asset_key: AssetKey, after_time: datetime.datetime
    ) -> ValidAssetSubset:
        return self._queryer.get_asset_subset_updated_after_time(
            asset_key=asset_key, after_time=after_time
        )

    def get_parent_asset_partitions_updated_after_child(
        self,
        *,
        asset_partition: AssetKeyPartitionKey,
        parent_asset_partitions: AbstractSet[AssetKeyPartitionKey],
        ignored_parent_keys: AbstractSet[AssetKey],
    ) -> AbstractSet[AssetKeyPartitionKey]:
        return self._queryer.get_parent_asset_partitions_updated_after_child(
            asset_partition=asset_partition,
            parent_asset_partitions=parent_asset_partitions,
            respect_materialization_data_versions=False,
            ignored_parent_keys=ignored_parent_keys,
        )


class SchedulingContext(NamedTuple):
    # the slice over which the condition is being evaluated
    candidate_slice: AssetSlice

    # the condition being evaluated
    condition: SchedulingCondition
    # a unique identifier for the condition within the broader tree
    condition_unique_id: str

    asset_graph_view: AssetGraphView

    # the context object for the parent condition
    parent_context: Optional["SchedulingContext"]

    # the time at which this context object was created
    create_time: datetime.datetime
    logger: logging.Logger

    # a cursor containing information about this asset calculated on the previous tick
    cursor: Optional[SchedulingConditionCursor]
    # a mapping of information computed on the current tick for assets which are upstream of this
    # asset
    current_tick_evaluation_info_by_key: Mapping[AssetKey, SchedulingEvaluationInfo]

    non_agv_instance_interface: NonAGVInstanceInterface

    # hack to avoid circular references during pydantic validation
    inner_legacy_context: Any
    is_legacy_evaluation: bool

    @staticmethod
    def create(
        asset_key: AssetKey,
        asset_graph_view: AssetGraphView,
        logger: logging.Logger,
        current_tick_evaluation_info_by_key: Mapping[AssetKey, SchedulingEvaluationInfo],
        previous_evaluation_info: Optional[SchedulingEvaluationInfo],
        legacy_context: "LegacyRuleEvaluationContext",
    ) -> "SchedulingContext":
        asset_graph = asset_graph_view.asset_graph
        auto_materialize_policy = check.not_none(asset_graph.get(asset_key).auto_materialize_policy)
        scheduling_condition = auto_materialize_policy.to_scheduling_condition()

        return SchedulingContext(
            candidate_slice=asset_graph_view.get_asset_slice(asset_key=asset_key),
            condition=scheduling_condition,
            condition_unique_id=scheduling_condition.get_unique_id(
                parent_unique_id=None, index=None
            ),
            asset_graph_view=asset_graph_view,
            parent_context=None,
            create_time=pendulum.now("UTC"),
            logger=logger,
            cursor=previous_evaluation_info.cursor if previous_evaluation_info else None,
            current_tick_evaluation_info_by_key=current_tick_evaluation_info_by_key,
            inner_legacy_context=legacy_context,
            non_agv_instance_interface=NonAGVInstanceInterface(
                asset_graph_view.get_inner_queryer_for_back_compat()
            ),
            is_legacy_evaluation=_has_legacy_condition(scheduling_condition),
        )

    def for_child_condition(
        self, child_condition: SchedulingCondition, child_index: int, candidate_slice: AssetSlice
    ) -> "SchedulingContext":
        return SchedulingContext(
            candidate_slice=candidate_slice,
            condition=child_condition,
            condition_unique_id=child_condition.get_unique_id(
                parent_unique_id=self.condition_unique_id, index=child_index
            ),
            asset_graph_view=self.asset_graph_view,
            parent_context=self,
            create_time=pendulum.now("UTC"),
            logger=self.logger,
            cursor=self.cursor,
            current_tick_evaluation_info_by_key=self.current_tick_evaluation_info_by_key,
            inner_legacy_context=self.inner_legacy_context.for_child(
                child_condition,
                child_condition.get_unique_id(
                    parent_unique_id=self.condition_unique_id, index=child_index
                ),
                candidate_slice.convert_to_valid_asset_subset(),
            ),
            non_agv_instance_interface=self.non_agv_instance_interface,
            is_legacy_evaluation=self.is_legacy_evaluation,
        )

    @property
    def asset_graph(self) -> "BaseAssetGraph":
        return self.asset_graph_view.asset_graph

    @property
    def asset_key(self) -> AssetKey:
        """The asset key over which this condition is being evaluated."""
        return self.candidate_slice.asset_key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """The partitions definition for the asset being evaluated, if it exists."""
        return self.asset_graph.get(self.asset_key).partitions_def

    @property
    def root_context(self) -> "SchedulingContext":
        """Returns the context object at the root of the condition evaluation tree."""
        return self.parent_context.root_context if self.parent_context is not None else self

    @property
    def node_cursor(self) -> Optional[SchedulingConditionNodeCursor]:
        """Returns the evaluation node for this node from the previous evaluation, if this node
        was evaluated on the previous tick.
        """
        if self.cursor is None:
            return None
        else:
            return self.cursor.node_cursors_by_unique_id.get(self.condition_unique_id)

    @property
    def previous_true_slice(self) -> Optional[AssetSlice]:
        """Returns the true slice for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        if self.node_cursor is None:
            return None
        else:
            return self.asset_graph_view.get_asset_slice_from_subset(self.node_cursor.true_subset)

    @property
    def effective_dt(self) -> datetime.datetime:
        return self.asset_graph_view.effective_dt

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return (
            self.inner_legacy_context
            if self.is_legacy_evaluation
            else check.failed(
                "Legacy access only allowed in AutoMaterializeRule subclasses in auto_materialize_rules_impls.py"
            )
        )

    @property
    def previous_requested_slice(self) -> Optional[AssetSlice]:
        """Returns the requested slice for the previous evaluation. If this asset has never been
        evaluated, returns None.
        """
        return (
            self.asset_graph_view.get_asset_slice_from_subset(self.cursor.previous_requested_subset)
            if self.cursor
            else None
        )

    @property
    def previous_candidate_slice(self) -> Optional[AssetSlice]:
        """Returns the candidate slice for the previous evaluation. If this node has never been
        evaluated, returns None.
        """
        candidate_subset = self.node_cursor.candidate_subset if self.node_cursor else None
        if isinstance(candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return self.asset_graph_view.get_asset_slice(asset_key=self.asset_key)
        else:
            return (
                self.asset_graph_view.get_asset_slice_from_subset(candidate_subset)
                if candidate_subset
                else None
            )

    @property
    def previous_evaluation_max_storage_id(self) -> Optional[int]:
        """Returns the maximum storage ID for the previous time this node was evaluated. If this
        node has never been evaluated, returns None.
        """
        return (
            self.cursor.temporal_context.last_event_id if self.cursor and self.node_cursor else None
        )

    @property
    def previous_evaluation_effective_dt(self) -> Optional[datetime.datetime]:
        """Returns the datetime for the previous time this node was evaluated. If this node has
        never been evaluated, returns None.
        """
        return (
            self.cursor.temporal_context.effective_dt if self.cursor and self.node_cursor else None
        )

    @property
    def new_max_storage_id(self) -> Optional[int]:
        if self.is_legacy_evaluation:
            # legacy evaluations handle event log tailing in a different manner, and so need to
            # use a different storage id cursoring scheme
            return self.legacy_context.new_max_storage_id
        else:
            return self.asset_graph_view.last_event_id
