import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Optional, Type, TypeVar

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.legacy.legacy_context import (
    LegacyRuleEvaluationContext,
)
from dagster._core.definitions.declarative_automation.legacy.rule_condition import RuleCondition
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionCursor,
    AutomationConditionNodeCursor,
    HistoricalAllPartitionsSubsetSentinel,
    StructuredCursor,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph

T_StructuredCursor = TypeVar("T_StructuredCursor", bound=StructuredCursor)


def _has_legacy_condition(condition: AutomationCondition):
    """Detects if the given condition has any legacy rules."""
    if isinstance(condition, RuleCondition):
        return True
    else:
        return any(_has_legacy_condition(child) for child in condition.children)


@dataclass(frozen=True)
class AutomationContext:
    condition: AutomationCondition
    condition_unique_id: str
    candidate_slice: AssetSlice

    create_time: datetime.datetime

    asset_graph_view: AssetGraphView
    current_tick_results_by_key: Mapping[AssetKey, AutomationResult]

    parent_context: Optional["AutomationContext"]

    _cursor: Optional[AutomationConditionCursor]
    _legacy_context: Optional[LegacyRuleEvaluationContext]

    _root_log: logging.Logger

    @staticmethod
    def create(
        asset_key: AssetKey,
        asset_graph_view: AssetGraphView,
        log: logging.Logger,
        current_tick_results_by_key: Mapping[AssetKey, AutomationResult],
        condition_cursor: Optional[AutomationConditionCursor],
        legacy_context: "LegacyRuleEvaluationContext",
    ) -> "AutomationContext":
        asset_graph = asset_graph_view.asset_graph
        condition = check.not_none(asset_graph.get(asset_key).automation_condition)
        condition_unqiue_id = condition.get_unique_id(parent_unique_id=None, index=None)

        return AutomationContext(
            condition=condition,
            condition_unique_id=condition_unqiue_id,
            candidate_slice=asset_graph_view.get_asset_slice(asset_key=asset_key),
            create_time=get_current_datetime(),
            asset_graph_view=asset_graph_view,
            current_tick_results_by_key=current_tick_results_by_key,
            parent_context=None,
            _cursor=condition_cursor,
            _legacy_context=legacy_context if condition.has_rule_condition else None,
            _root_log=log,
        )

    def for_child_condition(
        self, child_condition: AutomationCondition, child_index: int, candidate_slice: AssetSlice
    ) -> "AutomationContext":
        condition_unqiue_id = child_condition.get_unique_id(
            parent_unique_id=self.condition_unique_id, index=child_index
        )
        return AutomationContext(
            condition=child_condition,
            condition_unique_id=condition_unqiue_id,
            candidate_slice=candidate_slice,
            create_time=get_current_datetime(),
            asset_graph_view=self.asset_graph_view,
            current_tick_results_by_key=self.current_tick_results_by_key,
            parent_context=self,
            _cursor=self._cursor,
            _legacy_context=self._legacy_context.for_child(
                child_condition,
                condition_unqiue_id,
                candidate_slice.convert_to_valid_asset_subset(),
            )
            if self._legacy_context
            else None,
            _root_log=self._root_log,
        )

    @property
    def log(self) -> logging.Logger:
        """The logger for the current condition evaluation."""
        return self._root_log.getChild(self.condition.__class__.__name__)

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
    def root_context(self) -> "AutomationContext":
        """Returns the context object at the root of the condition evaluation tree."""
        return self.parent_context.root_context if self.parent_context is not None else self

    @property
    def _node_cursor(self) -> Optional[AutomationConditionNodeCursor]:
        """Returns the evaluation node for this node from the previous evaluation, if this node
        was evaluated on the previous tick.
        """
        check.invariant(
            self.condition.requires_cursor,
            f"Attempted to access cursor for a node of type {self.condition.__class__.__name__} "
            "which does not store a cursor. Set the `requires_cursor` property to `True` to enable access.",
        )

        return (
            self._cursor.node_cursors_by_unique_id.get(self.condition_unique_id)
            if self._cursor
            else None
        )

    @property
    def cursor(self) -> Optional[str]:
        """The cursor value returned on the previous evaluation for this condition, if any."""
        return self._node_cursor.get_structured_cursor(as_type=str) if self._node_cursor else None

    @property
    def previous_true_slice(self) -> Optional[AssetSlice]:
        """Returns the true slice for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        return (
            self.asset_graph_view.get_asset_slice_from_subset(self._node_cursor.true_subset)
            if self._node_cursor
            else None
        )

    @property
    def evaluation_time(self) -> datetime.datetime:
        """A consistent datetime for all evaluations on this tick."""
        return self.asset_graph_view.effective_dt

    @property
    def max_storage_id(self) -> Optional[int]:
        """A consistent maximum storage id to consider for all evaluations on this tick."""
        if self._legacy_context is not None:
            # legacy evaluations handle event log tailing in a different manner, and so need to
            # use a different storage id cursoring scheme
            return self.legacy_context.new_max_storage_id
        else:
            return self.asset_graph_view.last_event_id

    @property
    def previous_max_storage_id(self) -> Optional[int]:
        """The `max_storage_id` value used on the previous tick's evaluation."""
        return self._cursor.temporal_context.last_event_id if self._cursor else None

    @property
    def previous_evaluation_time(self) -> Optional[datetime.datetime]:
        """The `evaluation_time` value used on the previous tick's evaluation."""
        return self._cursor.temporal_context.effective_dt if self._cursor else None

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return check.not_none(
            self._legacy_context,
            "Cannot access legacy context unless evaluating a condition containing a RuleCondition.",
        )

    @property
    def previous_requested_slice(self) -> Optional[AssetSlice]:
        """Returns the requested slice for the previous evaluation. If this asset has never been
        evaluated, returns None.
        """
        return (
            self.asset_graph_view.get_asset_slice_from_subset(
                self._cursor.previous_requested_subset
            )
            if self._cursor
            else None
        )

    @property
    def previous_candidate_slice(self) -> Optional[AssetSlice]:
        """Returns the candidate slice for the previous evaluation. If this node has never been
        evaluated, returns None.
        """
        candidate_subset = self._node_cursor.candidate_subset if self._node_cursor else None
        if isinstance(candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return self.asset_graph_view.get_asset_slice(asset_key=self.asset_key)
        else:
            return (
                self.asset_graph_view.get_asset_slice_from_subset(candidate_subset)
                if candidate_subset
                else None
            )

    def get_empty_slice(self) -> AssetSlice:
        """Returns an empty AssetSlice of the currently-evaluated asset."""
        return self.asset_graph_view.get_empty_slice(asset_key=self.asset_key)

    def get_structured_cursor(
        self, as_type: Type[T_StructuredCursor]
    ) -> Optional[T_StructuredCursor]:
        return (
            self._node_cursor.get_structured_cursor(as_type=as_type) if self._node_cursor else None
        )
