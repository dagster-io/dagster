import datetime
import inspect
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey, T_EntityKey
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
from dagster._core.definitions.metadata import MetadataMapping
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
    from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
        AutomationConditionEvaluator,
    )

T_StructuredCursor = TypeVar("T_StructuredCursor", bound=StructuredCursor)

U_EntityKey = TypeVar("U_EntityKey", AssetKey, AssetCheckKey)


def _has_legacy_condition(condition: AutomationCondition):
    """Detects if the given condition has any legacy rules."""
    if isinstance(condition, RuleCondition):
        return True
    else:
        return any(_has_legacy_condition(child) for child in condition.children)


@dataclass(frozen=True)
class AutomationContext(Generic[T_EntityKey]):
    condition: AutomationCondition
    condition_unique_ids: Sequence[str]
    candidate_subset: EntitySubset[T_EntityKey]

    create_time: datetime.datetime

    asset_graph_view: AssetGraphView
    request_subsets_by_key: Mapping[EntityKey, EntitySubset]

    parent_context: Optional["AutomationContext"]

    _cursor: Optional[AutomationConditionCursor]
    _full_cursor: AssetDaemonCursor
    _legacy_context: Optional[LegacyRuleEvaluationContext]

    _root_log: logging.Logger

    @staticmethod
    def create(key: EntityKey, evaluator: "AutomationConditionEvaluator") -> "AutomationContext":
        asset_graph_view = evaluator.asset_graph_view
        condition = check.not_none(
            evaluator.asset_graph.get(key).automation_condition or evaluator.default_condition
        )
        unique_ids = condition.get_node_unique_ids(parent_unique_ids=[None], child_indices=[None])

        return AutomationContext(
            condition=condition,
            condition_unique_ids=unique_ids,
            candidate_subset=evaluator.asset_graph_view.get_full_subset(key=key),
            create_time=get_current_datetime(),
            asset_graph_view=asset_graph_view,
            request_subsets_by_key=evaluator.request_subsets_by_key,
            parent_context=None,
            _cursor=evaluator.cursor.get_previous_condition_cursor(key),
            _full_cursor=evaluator.cursor,
            _legacy_context=LegacyRuleEvaluationContext.create(key, evaluator)
            if condition.has_rule_condition and isinstance(key, AssetKey)
            else None,
            _root_log=evaluator.logger,
        )

    def for_child_condition(
        self,
        child_condition: AutomationCondition[U_EntityKey],
        child_indices: Sequence[Optional[int]],
        candidate_subset: EntitySubset[U_EntityKey],
    ) -> "AutomationContext[U_EntityKey]":
        check.invariant(len(child_indices) > 0, "Must be at least one child index")

        unique_ids = child_condition.get_node_unique_ids(
            parent_unique_ids=self.condition_unique_ids, child_indices=child_indices
        )
        return AutomationContext(
            condition=child_condition,
            condition_unique_ids=unique_ids,
            candidate_subset=candidate_subset,
            create_time=get_current_datetime(),
            asset_graph_view=self.asset_graph_view,
            request_subsets_by_key=self.request_subsets_by_key,
            parent_context=self,
            _cursor=self._cursor,
            _full_cursor=self._full_cursor,
            _legacy_context=self._legacy_context.for_child(
                child_condition, unique_ids[0], candidate_subset
            )
            if self._legacy_context
            else None,
            _root_log=self._root_log,
        )

    async def evaluate_async(self) -> AutomationResult[T_EntityKey]:
        if inspect.iscoroutinefunction(self.condition.evaluate):
            return await self.condition.evaluate(self)
        return self.condition.evaluate(self)

    @property
    def log(self) -> logging.Logger:
        """The logger for the current condition evaluation."""
        return self._root_log.getChild(self.condition.__class__.__name__)

    @property
    def asset_graph(self) -> "BaseAssetGraph":
        return self.asset_graph_view.asset_graph

    @property
    def key(self) -> T_EntityKey:
        """The asset key over which this condition is being evaluated."""
        return self.candidate_subset.key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """The partitions definition for the asset being evaluated, if it exists."""
        if isinstance(self.key, AssetKey):
            return self.asset_graph.get(self.key).partitions_def
        else:
            return None

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

        if not self._cursor:
            return None

        for unique_id in self.condition_unique_ids:
            if unique_id in self._cursor.node_cursors_by_unique_id:
                return self._cursor.node_cursors_by_unique_id[unique_id]

        return None

    @property
    def cursor(self) -> Optional[str]:
        """The cursor value returned on the previous evaluation for this condition, if any."""
        return self._node_cursor.get_structured_cursor(as_type=str) if self._node_cursor else None

    @property
    def previous_true_subset(self) -> Optional[EntitySubset[T_EntityKey]]:
        """Returns the true subset for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        return (
            self.asset_graph_view.get_subset_from_serializable_subset(self._node_cursor.true_subset)
            if self._node_cursor
            else None
        )

    @property
    def previous_metadata(self) -> Optional[MetadataMapping]:
        """Returns the metadata for this node from the previous evaluation, if this node was
        evaluated on the previous tick.
        """
        return self._node_cursor.metadata if self._node_cursor else None

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
    def previous_temporal_context(self) -> Optional[TemporalContext]:
        """The `temporal_context` value used on the previous tick's evaluation."""
        return self._cursor.temporal_context if self._cursor else None

    @property
    def evaluation_id(self) -> int:
        """Returns the current evaluation ID. This ID is incremented for each tick
        and is global across all conditions.
        """
        return self._full_cursor.evaluation_id

    @property
    def legacy_context(self) -> LegacyRuleEvaluationContext:
        return check.not_none(
            self._legacy_context,
            "Cannot access legacy context unless evaluating a condition containing a RuleCondition.",
        )

    @property
    def previous_candidate_subset(self) -> Optional[EntitySubset[T_EntityKey]]:
        """Returns the candidate subset for the previous evaluation. If this node has never been
        evaluated, returns None.
        """
        candidate_subset = self._node_cursor.candidate_subset if self._node_cursor else None
        if isinstance(candidate_subset, HistoricalAllPartitionsSubsetSentinel):
            return self.asset_graph_view.get_full_subset(key=self.key)
        else:
            return (
                self.asset_graph_view.get_subset_from_serializable_subset(candidate_subset)
                if candidate_subset
                else None
            )

    def get_previous_requested_subset(
        self, key: T_EntityKey
    ) -> Optional[EntitySubset[T_EntityKey]]:
        """Returns the requested subset for the previous evaluation. If the entity has never been
        evaluated, returns None.
        """
        cursor = self._full_cursor.get_previous_condition_cursor(key)
        if cursor is None:
            return None
        return self.asset_graph_view.get_subset_from_serializable_subset(
            cursor.previous_requested_subset
        )

    def get_empty_subset(self) -> EntitySubset[T_EntityKey]:
        """Returns an empty EntitySubset of the currently-evaluated key."""
        return self.asset_graph_view.get_empty_subset(key=self.key)

    def get_structured_cursor(
        self, as_type: type[T_StructuredCursor]
    ) -> Optional[T_StructuredCursor]:
        return (
            self._node_cursor.get_structured_cursor(as_type=as_type) if self._node_cursor else None
        )
