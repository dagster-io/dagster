import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Optional

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
    TemporalContext,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.legacy.rule_condition import RuleCondition
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionCursor,
    AutomationConditionNodeCursor,
    HistoricalAllPartitionsSubsetSentinel,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._time import get_current_datetime

from .legacy.legacy_context import LegacyRuleEvaluationContext

if TYPE_CHECKING:
    from dagster._core.definitions.base_asset_graph import BaseAssetGraph


def _has_legacy_condition(condition: AutomationCondition):
    """Detects if the given condition has any legacy rules."""
    if isinstance(condition, RuleCondition):
        return True
    else:
        return any(_has_legacy_condition(child) for child in condition.children)


@dataclass
class AutomationContext:
    condition: AutomationCondition
    condition_unique_id: str
    candidate_slice: AssetSlice

    logger: logging.Logger
    create_time: datetime.datetime

    asset_graph_view: AssetGraphView
    current_tick_results_by_key: Mapping[AssetKey, AutomationResult]

    parent_context: Optional["AutomationContext"]

    _cursor: Optional[AutomationConditionCursor]
    _legacy_context: LegacyRuleEvaluationContext
    _is_legacy_evaluation: bool

    @staticmethod
    def create(
        asset_key: AssetKey,
        asset_graph_view: AssetGraphView,
        logger: logging.Logger,
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
            logger=logger,
            create_time=get_current_datetime(),
            asset_graph_view=asset_graph_view,
            current_tick_results_by_key=current_tick_results_by_key,
            parent_context=None,
            _cursor=condition_cursor,
            _legacy_context=legacy_context,
            _is_legacy_evaluation=_has_legacy_condition(condition),
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
            logger=self.logger,
            create_time=get_current_datetime(),
            asset_graph_view=self.asset_graph_view,
            current_tick_results_by_key=self.current_tick_results_by_key,
            parent_context=self,
            _cursor=self._cursor,
            _legacy_context=self._legacy_context.for_child(
                child_condition,
                condition_unqiue_id,
                candidate_slice.convert_to_valid_asset_subset(),
            ),
            _is_legacy_evaluation=self._is_legacy_evaluation,
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
    def root_context(self) -> "AutomationContext":
        """Returns the context object at the root of the condition evaluation tree."""
        return self.parent_context.root_context if self.parent_context is not None else self

    @property
    def node_cursor(self) -> Optional[AutomationConditionNodeCursor]:
        """Returns the evaluation node for this node from the previous evaluation, if this node
        was evaluated on the previous tick.
        """
        return (
            self._cursor.node_cursors_by_unique_id.get(self.condition_unique_id)
            if self._cursor
            else None
        )

    @property
    def previous_true_slice(self) -> Optional[AssetSlice]:
        """Returns the true slice for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        return (
            self.asset_graph_view.get_asset_slice_from_subset(self.node_cursor.true_subset)
            if self.node_cursor
            else None
        )

    @property
    def effective_dt(self) -> datetime.datetime:
        return self.asset_graph_view.effective_dt

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return (
            self._legacy_context
            if self._is_legacy_evaluation
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
        """Returns the maximum storage ID for the previous time this asset was evaluated."""
        return self._cursor.temporal_context.last_event_id if self._cursor else None

    @property
    def previous_evaluation_effective_dt(self) -> Optional[datetime.datetime]:
        """Returns the datetime for the previous time this asset was evaluated."""
        return self._cursor.temporal_context.effective_dt if self._cursor else None

    @property
    def new_max_storage_id(self) -> Optional[int]:
        if self._is_legacy_evaluation:
            # legacy evaluations handle event log tailing in a different manner, and so need to
            # use a different storage id cursoring scheme
            return self.legacy_context.new_max_storage_id
        else:
            return self.asset_graph_view.last_event_id

    @property
    def new_temporal_context(self) -> TemporalContext:
        return TemporalContext(
            effective_dt=self.effective_dt, last_event_id=self.new_max_storage_id
        )
