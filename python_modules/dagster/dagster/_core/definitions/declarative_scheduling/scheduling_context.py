import datetime
import logging
from typing import TYPE_CHECKING, Any, Mapping, Optional

import pendulum

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    SchedulingEvaluationInfo,
    SchedulingEvaluationResultNode,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._model import DagsterModel

from .legacy.legacy_context import LegacyRuleEvaluationContext

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class SchedulingContext(DagsterModel):
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

    # hack to avoid circular references during pydantic validation
    inner_legacy_context: Any

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

        # construct is used here for performance
        return SchedulingContext.construct(
            candidate_slice=asset_graph_view.get_asset_slice(asset_key),
            condition=scheduling_condition,
            condition_unique_id=scheduling_condition.get_unique_id(None),
            asset_graph_view=asset_graph_view,
            parent_context=None,
            create_time=pendulum.now("UTC"),
            logger=logger,
            previous_evaluation_info=previous_evaluation_info,
            current_tick_evaluation_info_by_key=current_tick_evaluation_info_by_key,
            inner_legacy_context=legacy_context,
        )

    def for_child_condition(
        self, child_condition: SchedulingCondition, candidate_slice: AssetSlice
    ) -> "SchedulingContext":
        # construct is used here for performance
        return SchedulingContext.construct(
            candidate_slice=candidate_slice,
            condition=child_condition,
            condition_unique_id=child_condition.get_unique_id(
                parent_unique_id=self.condition_unique_id
            ),
            asset_graph_view=self.asset_graph_view,
            parent_context=self,
            create_time=pendulum.now("UTC"),
            logger=self.logger,
            previous_evaluation_info=self.previous_evaluation_info,
            current_tick_evaluation_info_by_key=self.current_tick_evaluation_info_by_key,
            inner_legacy_context=self.legacy_context.for_child(
                child_condition,
                child_condition.get_unique_id(self.condition_unique_id),
                candidate_slice.convert_to_valid_asset_subset(),
            ),
        )

    @property
    def asset_key(self) -> AssetKey:
        """The asset key over which this condition is being evaluated."""
        return self.candidate_slice.asset_key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """The partitions definition for the asset being evaluated, if it exists."""
        return self.asset_graph_view.asset_graph.get(self.asset_key).partitions_def

    @property
    def root_context(self) -> "SchedulingContext":
        """Returns the context object at the root of the condition evaluation tree."""
        return self.parent_context.root_context if self.parent_context is not None else self

    @property
    def previous_evaluation_node(self) -> Optional[SchedulingEvaluationResultNode]:
        """Returns the evaluation node for this asset from the previous evaluation, if this node
        was evaluated on the previous tick.
        """
        if self.previous_evaluation_info is None:
            return None
        else:
            return self.previous_evaluation_info.get_evaluation_node(self.condition_unique_id)

    @property
    def effective_dt(self) -> datetime.datetime:
        return self.asset_graph_view.effective_dt

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return self.inner_legacy_context

    @property
    def _queryer(self) -> "CachingInstanceQueryer":
        return self.asset_graph_view._queryer  # noqa

    @property
    def new_max_storage_id(self) -> Optional[int]:
        # TODO: pull this from the AssetGraphView instead
        return self.legacy_context.new_max_storage_id

    def asset_updated_since_previous_tick(self) -> bool:
        """Returns True if the target asset has been updated since the previous evaluation."""
        cursor = (
            self.previous_evaluation_info.temporal_context.last_event_id
            if self.previous_evaluation_info
            else None
        )
        return self._queryer.asset_partition_has_materialization_or_observation(
            asset_partition=AssetKeyPartitionKey(self.asset_key),
            after_cursor=cursor,
        )
