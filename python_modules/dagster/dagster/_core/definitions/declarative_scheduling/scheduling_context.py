import datetime
import logging
from typing import TYPE_CHECKING, AbstractSet, Any, Mapping, NamedTuple, Optional

import pendulum

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    SchedulingEvaluationInfo,
    SchedulingEvaluationResultNode,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    PartitionsDefinition,
)

from .legacy.legacy_context import LegacyRuleEvaluationContext

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


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

    # a SchedulingEvaluationInfo object representing information about the full evaluation tree
    # from the previous tick, if this asset was evaluated on the previous tick
    previous_evaluation_info: Optional[SchedulingEvaluationInfo]
    # a mapping of information computed on the current tick for assets which are upstream of this
    # asset
    current_tick_evaluation_info_by_key: Mapping[AssetKey, SchedulingEvaluationInfo]

    non_agv_instance_interface: NonAGVInstanceInterface

    # hack to avoid circular references during pydantic validation
    inner_legacy_context: Any
    allow_legacy_access: bool

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
            candidate_slice=asset_graph_view.get_asset_slice(asset_key),
            condition=scheduling_condition,
            condition_unique_id=scheduling_condition.get_unique_id(
                parent_unique_id=None, index=None
            ),
            asset_graph_view=asset_graph_view,
            parent_context=None,
            create_time=pendulum.now("UTC"),
            logger=logger,
            previous_evaluation_info=previous_evaluation_info,
            current_tick_evaluation_info_by_key=current_tick_evaluation_info_by_key,
            inner_legacy_context=legacy_context,
            non_agv_instance_interface=NonAGVInstanceInterface(
                asset_graph_view.get_inner_queryer_for_back_compat()
            ),
            allow_legacy_access=False,
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
            previous_evaluation_info=self.previous_evaluation_info,
            current_tick_evaluation_info_by_key=self.current_tick_evaluation_info_by_key,
            inner_legacy_context=self.inner_legacy_context.for_child(
                child_condition,
                child_condition.get_unique_id(
                    parent_unique_id=self.condition_unique_id, index=child_index
                ),
                candidate_slice.convert_to_valid_asset_subset(),
            ),
            non_agv_instance_interface=self.non_agv_instance_interface,
            allow_legacy_access=self.allow_legacy_access,
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
    def previous_evaluation_node(self) -> Optional[SchedulingEvaluationResultNode]:
        """Returns the evaluation node for this node from the previous evaluation, if this node
        was evaluated on the previous tick.
        """
        if self.previous_evaluation_info is None:
            return None
        else:
            return self.previous_evaluation_info.get_evaluation_node(self.condition_unique_id)

    @property
    def previous_true_slice(self) -> Optional[AssetSlice]:
        """Returns the true slice for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        if self.previous_evaluation_node is None:
            return None
        else:
            return self.previous_evaluation_node.true_slice

    @property
    def effective_dt(self) -> datetime.datetime:
        return self.asset_graph_view.effective_dt

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return (
            self.inner_legacy_context
            if self.allow_legacy_access
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
            self.previous_evaluation_info.requested_slice if self.previous_evaluation_info else None
        )

    @property
    def previous_candidate_slice(self) -> Optional[AssetSlice]:
        """Returns the candidate slice for the previous evaluation. If this node has never been
        evaluated, returns None.
        """
        return (
            self.previous_evaluation_node.candidate_slice if self.previous_evaluation_node else None
        )

    @property
    def previous_evaluation_max_storage_id(self) -> Optional[int]:
        """Returns the maximum storage ID for the previous time this node was evaluated. If this
        node has never been evaluated, returns None.
        """
        return (
            (self.previous_evaluation_info.temporal_context.last_event_id or 0)
            if self.previous_evaluation_info and self.previous_evaluation_node
            else None
        )

    @property
    def previous_evaluation_effective_dt(self) -> Optional[datetime.datetime]:
        """Returns the datetime for the previous time this node was evaluated. If this node has
        never been evaluated, returns None.
        """
        return (
            self.previous_evaluation_info.temporal_context.effective_dt
            if self.previous_evaluation_info and self.previous_evaluation_node
            else None
        )

    @property
    def new_max_storage_id(self) -> Optional[int]:
        # TODO: pull this from the AssetGraphView instead
        return self.inner_legacy_context.new_max_storage_id
