import datetime
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Generic, Mapping, Optional, Sequence

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import (
    AssetCheckKey,
    AssetKey,
    CoercibleToAssetKey,
    T_EntityKey,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionCursor,
    AutomationConditionEvaluation,
    AutomationConditionNodeCursor,
    AutomationConditionNodeSnapshot,
    AutomationConditionSnapshot,
    get_serializable_candidate_subset,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsSubset
from dagster._record import copy, record
from dagster._serdes.serdes import is_whitelisted_for_serdes_object
from dagster._time import get_current_timestamp
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )
    from dagster._core.definitions.declarative_automation.operators import AndAutomationCondition
    from dagster._core.definitions.declarative_automation.operators.dep_operators import (
        DepsAutomationCondition,
    )


class AutomationCondition(ABC, Generic[T_EntityKey]):
    """An AutomationCondition represents a condition of an asset that impacts whether it should be
    automatically executed. For example, you can have a condition which becomes true whenever the
    code version of the asset is changed, or whenever an upstream dependency is updated.

    .. code-block:: python

        from dagster import AutomationCondition, asset

        @asset(automation_condition=AutomationCondition.on_cron("0 0 * * *"))
        def my_asset(): ...

    AutomationConditions may be combined together into expressions using a variety of operators.

    .. code-block:: python

        from dagster import AssetSelection, AutomationCondition, asset

        # any dependencies from the "important" group are missing
        any_important_deps_missing = AutomationCondition.any_deps_match(
            AutomationCondition.missing(),
        ).allow(AssetSelection.groups("important"))

        # there is a new code version for this asset since the last time it was requested
        new_code_version = AutomationCondition.code_version_changed().since(
            AutomationCondition.newly_requested()
        )

        # there is a new code version and no important dependencies are missing
        my_condition = new_code_version & ~any_important_deps_missing

        @asset(automation_condition=my_condition)
        def my_asset(): ...

    """

    @property
    def requires_cursor(self) -> bool:
        return True

    @property
    def children(self) -> Sequence["AutomationCondition"]:
        return []

    @property
    def description(self) -> str:
        """Human-readable description of when this condition is true."""
        return ""

    @property
    def name(self) -> str:
        """Formal name of this specific condition, generally aligning with its static constructor."""
        return self.__class__.__name__

    def get_label(self) -> Optional[str]:
        return None

    def get_node_snapshot(self, unique_id: str) -> AutomationConditionNodeSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AutomationConditionNodeSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
            label=self.get_label(),
            name=self.name,
        )

    def get_snapshot(
        self, *, parent_unique_id: Optional[str] = None, index: Optional[int] = None
    ) -> AutomationConditionSnapshot:
        """Returns a serializable snapshot of the entire AutomationCondition tree."""
        unique_id = self.get_node_unique_id(parent_unique_id=parent_unique_id, index=index)
        node_snapshot = self.get_node_snapshot(unique_id)
        children = [
            child.get_snapshot(parent_unique_id=unique_id, index=i)
            for (i, child) in enumerate(self.children)
        ]
        return AutomationConditionSnapshot(node_snapshot=node_snapshot, children=children)

    def get_node_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), str(index), self.name]
        return non_secure_md5_hash_str("".join(parts).encode())

    def get_unique_id(
        self, *, parent_node_unique_id: Optional[str] = None, index: Optional[int] = None
    ) -> str:
        """Returns a unique identifier for the entire subtree."""
        node_unique_id = self.get_node_unique_id(
            parent_unique_id=parent_node_unique_id, index=index
        )
        child_unique_ids = [
            child.get_unique_id(parent_node_unique_id=node_unique_id, index=i)
            for i, child in enumerate(self.children)
        ]
        return non_secure_md5_hash_str("".join([node_unique_id, *child_unique_ids]).encode())

    def __hash__(self) -> int:
        return hash(self.get_unique_id())

    @property
    def has_rule_condition(self) -> bool:
        from dagster._core.definitions.declarative_automation.legacy import RuleCondition

        if isinstance(self, RuleCondition):
            return True
        return any(child.has_rule_condition for child in self.children)

    @property
    def is_serializable(self) -> bool:
        if not is_whitelisted_for_serdes_object(self):
            return False
        return all(child.is_serializable for child in self.children)

    def as_auto_materialize_policy(self) -> "AutoMaterializePolicy":
        """Returns an AutoMaterializePolicy which contains this condition."""
        from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

        return AutoMaterializePolicy.from_automation_condition(self)

    @abstractmethod
    def evaluate(
        self, context: "AutomationContext[T_EntityKey]"
    ) -> "AutomationResult[T_EntityKey]":
        raise NotImplementedError()

    def __and__(
        self, other: "AutomationCondition[T_EntityKey]"
    ) -> "AndAutomationCondition[T_EntityKey]":
        from dagster._core.definitions.declarative_automation.operators import (
            AndAutomationCondition,
        )

        # group AndAutomationConditions together
        if isinstance(self, AndAutomationCondition):
            return AndAutomationCondition(operands=[*self.operands, other])
        return AndAutomationCondition(operands=[self, other])

    def __or__(
        self, other: "AutomationCondition[T_EntityKey]"
    ) -> "BuiltinAutomationCondition[T_EntityKey]":
        from dagster._core.definitions.declarative_automation.operators import OrAutomationCondition

        # group OrAutomationConditions together
        if isinstance(self, OrAutomationCondition):
            return OrAutomationCondition(operands=[*self.operands, other])
        return OrAutomationCondition(operands=[self, other])

    def __invert__(self) -> "BuiltinAutomationCondition[T_EntityKey]":
        from dagster._core.definitions.declarative_automation.operators import (
            NotAutomationCondition,
        )

        return NotAutomationCondition(operand=self)

    def since(
        self, reset_condition: "AutomationCondition[T_EntityKey]"
    ) -> "BuiltinAutomationCondition[T_EntityKey]":
        """Returns an AutomationCondition that is true if this condition has become true since the
        last time the reference condition became true.
        """
        from dagster._core.definitions.declarative_automation.operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=reset_condition)

    def newly_true(self) -> "BuiltinAutomationCondition[T_EntityKey]":
        """Returns an AutomationCondition that is true only on the tick that this condition goes
        from false to true for a given target.
        """
        from dagster._core.definitions.declarative_automation.operators import NewlyTrueCondition

        return NewlyTrueCondition(operand=self)

    def since_last_handled(self: "AutomationCondition") -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if this condition has become true since the
        target was last requested or updated, and since the last time this target's condition was modified.
        """
        with disable_dagster_warnings():
            return self.since(
                (
                    AutomationCondition.newly_requested()
                    | AutomationCondition.newly_updated()
                    | AutomationCondition.initial_evaluation()
                ).with_label("handled")
            )

    @public
    @experimental
    @staticmethod
    def asset_matches(
        key: "CoercibleToAssetKey", condition: "AutomationCondition[AssetKey]"
    ) -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if this condition is true for the given key."""
        from dagster._core.definitions.declarative_automation.operators import (
            EntityMatchesCondition,
        )

        asset_key = AssetKey.from_coercible(key)
        return EntityMatchesCondition(key=asset_key, operand=condition)

    @public
    @experimental
    @staticmethod
    def any_deps_match(condition: "AutomationCondition") -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true for a if at least one partition
        of the any of the target's dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this target's dependencies.
        """
        from dagster._core.definitions.declarative_automation.operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @public
    @experimental
    @staticmethod
    def all_deps_match(condition: "AutomationCondition") -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true for a if at least one partition
        of the all of the target's dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this target's dependencies.
        """
        from dagster._core.definitions.declarative_automation.operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @public
    @experimental
    @staticmethod
    def any_checks_match(
        condition: "AutomationCondition[AssetCheckKey]", blocking_only: bool = False
    ) -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true for if at least one of the target's
        checks evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's checks.
            blocking_only (bool): Determines if this condition will only be evaluated against blocking
                checks. Defaults to False.
        """
        from dagster._core.definitions.declarative_automation.operators import AnyChecksCondition

        return AnyChecksCondition(operand=condition, blocking_only=blocking_only)

    @public
    @experimental
    @staticmethod
    def all_checks_match(
        condition: "AutomationCondition[AssetCheckKey]", blocking_only: bool = False
    ) -> "BuiltinAutomationCondition[AssetKey]":
        """Returns an AutomationCondition that is true for an asset partition if all of its checks
        evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's checks.
            blocking_only (bool): Determines if this condition will only be evaluated against blocking
                checks. Defaults to False.
        """
        from dagster._core.definitions.declarative_automation.operators import AllChecksCondition

        return AllChecksCondition(operand=condition, blocking_only=blocking_only)

    @public
    @experimental
    @staticmethod
    def missing() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target has not been executed."""
        from dagster._core.definitions.declarative_automation.operands import (
            MissingAutomationCondition,
        )

        return MissingAutomationCondition()

    @public
    @experimental
    @staticmethod
    def run_in_progress() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target is part of an in-progress run."""
        from dagster._core.definitions.declarative_automation.operands import (
            RunInProgressAutomationCondition,
        )

        return RunInProgressAutomationCondition()

    @public
    @experimental
    @staticmethod
    def backfill_in_progress() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target is part of an in-progress backfill."""
        from dagster._core.definitions.declarative_automation.operands import (
            BackfillInProgressAutomationCondition,
        )

        return BackfillInProgressAutomationCondition()

    @public
    @experimental
    @staticmethod
    def execution_failed() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the latest execution of the target failed."""
        from dagster._core.definitions.declarative_automation.operands import (
            ExecutionFailedAutomationCondition,
        )

        return ExecutionFailedAutomationCondition()

    @public
    @experimental
    @staticmethod
    def in_progress() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true for an asset partition if it is part of an
        in-progress run or backfill.
        """
        return (
            AutomationCondition.run_in_progress() | AutomationCondition.backfill_in_progress()
        ).with_label("in_progress")

    @public
    @experimental
    @staticmethod
    def check_passed() -> "BuiltinAutomationCondition[AssetCheckKey]":
        """Returns an AutomationCondition that is true for an asset check if it has evaluated against
        the latest materialization of an asset and passed.
        """
        from dagster._core.definitions.declarative_automation.operands import CheckResultCondition

        return CheckResultCondition(passed=True)

    @public
    @experimental
    @staticmethod
    def check_failed() -> "BuiltinAutomationCondition[AssetCheckKey]":
        """Returns an AutomationCondition that is true for an asset check if it has evaluated against
        the latest materialization of an asset and failed.
        """
        from dagster._core.definitions.declarative_automation.operands import CheckResultCondition

        return CheckResultCondition(passed=False)

    @public
    @experimental
    @staticmethod
    def initial_evaluation() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true on the first evaluation of the expression."""
        from dagster._core.definitions.declarative_automation.operands import (
            InitialEvaluationCondition,
        )

        return InitialEvaluationCondition()

    @public
    @experimental
    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true when the target it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if this is used on a daily-partitioned asset with a lookback_delta of
                48 hours, this will return the latest two partitions.
        """
        from dagster._core.definitions.declarative_automation.operands import (
            InLatestTimeWindowCondition,
        )

        return InLatestTimeWindowCondition.from_lookback_delta(lookback_delta)

    @public
    @experimental
    @staticmethod
    def will_be_requested() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target will be requested this tick."""
        from dagster._core.definitions.declarative_automation.operands import (
            WillBeRequestedCondition,
        )

        return WillBeRequestedCondition()

    @public
    @experimental
    @staticmethod
    def newly_updated() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target has been updated since the previous tick."""
        from dagster._core.definitions.declarative_automation.operands import NewlyUpdatedCondition

        return NewlyUpdatedCondition()

    @public
    @experimental
    @staticmethod
    def newly_requested() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true if the target was requested on the previous tick."""
        from dagster._core.definitions.declarative_automation.operands import (
            NewlyRequestedCondition,
        )

        return NewlyRequestedCondition()

    @public
    @experimental
    @staticmethod
    def code_version_changed() -> "BuiltinAutomationCondition[AssetKey]":
        """Returns an AutomationCondition that is true if the target's code version has been changed
        since the previous tick.
        """
        from dagster._core.definitions.declarative_automation.operands.operands import (
            CodeVersionChangedCondition,
        )

        return CodeVersionChangedCondition()

    @public
    @experimental
    @staticmethod
    def cron_tick_passed(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is whenever a cron tick of the provided schedule is passed."""
        from dagster._core.definitions.declarative_automation.operands import (
            CronTickPassedCondition,
        )

        return CronTickPassedCondition(cron_schedule=cron_schedule, cron_timezone=cron_timezone)

    @experimental
    @staticmethod
    def newly_missing() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition that is true on the tick that the target becomes missing."""
        with disable_dagster_warnings():
            return AutomationCondition.missing().newly_true().with_label("newly_missing")

    @experimental
    @staticmethod
    def any_deps_updated() -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true if the target has at least one dependency
        that has updated since the previous tick, or will be requested on this tick.

        Will ignore parent updates if the run that updated the parent also plans to update
        the asset or check that this condition is applied to.
        """
        with disable_dagster_warnings():
            return AutomationCondition.any_deps_match(
                AutomationCondition.newly_updated() | AutomationCondition.will_be_requested()
            ).with_label("any_deps_updated")

    @experimental
    @staticmethod
    def any_deps_missing() -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true if the target has at least one dependency
        that is missing, and will not be requested on this tick.
        """
        with disable_dagster_warnings():
            return AutomationCondition.any_deps_match(
                AutomationCondition.missing() & ~AutomationCondition.will_be_requested()
            ).with_label("any_deps_missing")

    @experimental
    @staticmethod
    def any_deps_in_progress() -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true if the target has at least one dependency
        that is in progress.
        """
        with disable_dagster_warnings():
            return AutomationCondition.any_deps_match(AutomationCondition.in_progress()).with_label(
                "any_deps_in_progress"
            )

    @experimental
    @staticmethod
    def all_deps_blocking_checks_passed() -> "DepsAutomationCondition":
        """Returns an AutomationCondition that is true for any partition where all upstream
        blocking checks have passed, or will be requested on this tick.

        In-tick requests are allowed to enable creating runs that target both a parent with
        blocking checks and a child. Even though the checks have not currently passed, if
        they fail within the run, the run machinery will prevent the child from being
        materialized.
        """
        with disable_dagster_warnings():
            return AutomationCondition.all_deps_match(
                AutomationCondition.all_checks_match(
                    AutomationCondition.check_passed() | AutomationCondition.will_be_requested(),
                    blocking_only=True,
                ).with_label("all_blocking_checks_passed")
            ).with_label("all_deps_blocking_checks_passed")

    @experimental
    @staticmethod
    def all_deps_updated_since_cron(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "DepsAutomationCondition":
        """Returns an AutomatonCondition that is true if all of the target's dependencies have
        updated since the latest tick of the provided cron schedule.
        """
        with disable_dagster_warnings():
            return AutomationCondition.all_deps_match(
                AutomationCondition.newly_updated().since(
                    AutomationCondition.cron_tick_passed(cron_schedule, cron_timezone)
                )
                | AutomationCondition.will_be_requested()
            ).with_label(f"all_deps_updated_since_cron({cron_schedule}, {cron_timezone})")

    @public
    @experimental
    @staticmethod
    def eager() -> "AndAutomationCondition":
        """Returns an AutomationCondition which will cause a target to be executed if any of
        its dependencies update, and will execute missing partitions if they become missing
        after this condition is applied to the target.

        This will not execute targets that have any missing or in progress dependencies, or
        are currently in progress.

        For time partitioned assets, only the latest time partition will be considered.
        """
        with disable_dagster_warnings():
            return (
                AutomationCondition.in_latest_time_window()
                & (
                    AutomationCondition.newly_missing() | AutomationCondition.any_deps_updated()
                ).since_last_handled()
                & ~AutomationCondition.any_deps_missing()
                & ~AutomationCondition.any_deps_in_progress()
                & ~AutomationCondition.in_progress()
            ).with_label("eager")

    @public
    @experimental
    @staticmethod
    def on_cron(cron_schedule: str, cron_timezone: str = "UTC") -> "AndAutomationCondition":
        """Returns an AutomationCondition which will cause a target to be executed on a given
        cron schedule, after all of its dependencies have been updated since the latest
        tick of that cron schedule.

        For time partitioned assets, only the latest time partition will be considered.
        """
        with disable_dagster_warnings():
            return (
                AutomationCondition.in_latest_time_window()
                & AutomationCondition.cron_tick_passed(
                    cron_schedule, cron_timezone
                ).since_last_handled()
                & AutomationCondition.all_deps_updated_since_cron(cron_schedule, cron_timezone)
            ).with_label(f"on_cron({cron_schedule}, {cron_timezone})")

    @public
    @experimental
    @staticmethod
    def on_missing() -> "AndAutomationCondition":
        """Returns an AutomationCondition which will execute partitions of the target that
        are added after this condition is applied to the asset.

        This will not execute targets that have any missing dependencies.

        For time partitioned assets, only the latest time partition will be considered.
        """
        with disable_dagster_warnings():
            return (
                AutomationCondition.in_latest_time_window()
                & (
                    AutomationCondition.missing()
                    .newly_true()
                    .since_last_handled()
                    .with_label("missing_since_last_handled")
                )
                & ~AutomationCondition.any_deps_missing()
            ).with_label("on_missing")

    @public
    @experimental
    @staticmethod
    def any_downstream_conditions() -> "BuiltinAutomationCondition":
        """Returns an AutomationCondition which represents the union of all distinct downstream conditions."""
        from dagster._core.definitions.declarative_automation.operators import (
            AnyDownstreamConditionsCondition,
        )

        return AnyDownstreamConditionsCondition()


@record
class BuiltinAutomationCondition(AutomationCondition[T_EntityKey]):
    """Base class for AutomationConditions provided by the core dagster framework."""

    label: Optional[str] = None

    def get_label(self) -> Optional[str]:
        return self.label

    @public
    def with_label(self, label: Optional[str]) -> Self:
        """Returns a copy of this AutomationCondition with a human-readable label."""
        return copy(self, label=label)


class AutomationResult(Generic[T_EntityKey]):
    """The result of evaluating an AutomationCondition."""

    def __init__(
        self,
        context: "AutomationContext",
        true_subset: EntitySubset[T_EntityKey],
        cursor: Optional[str] = None,
        child_results: Optional[Sequence["AutomationResult"]] = None,
        **kwargs,
    ):
        from dagster._core.definitions.declarative_automation.automation_context import (
            AutomationContext,
        )

        self._context = check.inst_param(context, "context", AutomationContext)
        self._true_subset = check.inst_param(true_subset, "true_subset", EntitySubset)
        self._child_results = check.opt_sequence_param(
            child_results, "child_results", of_type=AutomationResult
        )

        self._start_timestamp = context.create_time.timestamp()
        self._end_timestamp = get_current_timestamp()

        # hidden_param which should only be set by legacy RuleConditions
        self._subsets_with_metadata = check.opt_sequence_param(
            kwargs.get("subsets_with_metadata"), "subsets_with_metadata", AssetSubsetWithMetadata
        )

        # hidden_param which should only be set by builtin conditions which require high performance
        # in their serdes layer
        structured_cursor = kwargs.get("structured_cursor")
        invalid_hidden_params = set(kwargs.keys()) - {"subsets_with_metadata", "structured_cursor"}
        check.param_invariant(
            not invalid_hidden_params, "kwargs", f"Invalid hidden params: {invalid_hidden_params}"
        )
        check.param_invariant(
            not (cursor and structured_cursor),
            "structured_cursor",
            "Cannot provide both cursor and structured_cursor.",
        )
        self._extra_state = check.opt_str_param(cursor, "cursor") or structured_cursor

        # used to enable the evaluator class to modify the evaluation in some edge cases
        self._serializable_subset_override: Optional[SerializableEntitySubset] = None

    @property
    def key(self) -> T_EntityKey:
        return self._true_subset.key

    @property
    def true_subset(self) -> EntitySubset[T_EntityKey]:
        return self._true_subset

    @property
    def start_timestamp(self) -> float:
        return self._start_timestamp

    @property
    def end_timestamp(self) -> float:
        return self._end_timestamp

    @property
    def child_results(self) -> Sequence["AutomationResult"]:
        return self._child_results

    @property
    def condition(self) -> AutomationCondition:
        return self._context.condition

    @property
    def condition_unique_id(self) -> str:
        return self._context.condition_unique_id

    @cached_property
    def value_hash(self) -> str:
        """An identifier for the contents of this AutomationResult. This will be identical for
        results with identical values, allowing us to avoid storing redundant information.
        """
        components: Sequence[str] = [
            self.condition_unique_id,
            self.condition.description,
            _compute_subset_value_str(self.get_serializable_subset()),
            _compute_subset_value_str(
                self._context.candidate_subset.convert_to_serializable_subset()
            ),
            *(_compute_subset_with_metadata_value_str(swm) for swm in self._subsets_with_metadata),
            *(child_result.value_hash for child_result in self._child_results),
        ]
        return non_secure_md5_hash_str("".join(components).encode("utf-8"))

    @cached_property
    def node_cursor(self) -> Optional[AutomationConditionNodeCursor]:
        """Cursor value storing information about this specific evaluation node, if required."""
        if not self.condition.requires_cursor:
            return None
        return AutomationConditionNodeCursor(
            true_subset=self.get_serializable_subset(),
            candidate_subset=get_serializable_candidate_subset(
                self._context.candidate_subset.convert_to_serializable_subset()
            ),
            subsets_with_metadata=self._subsets_with_metadata,
            extra_state=self._extra_state,
        )

    @property
    def serializable_evaluation(self) -> AutomationConditionEvaluation:
        return AutomationConditionEvaluation(
            condition_snapshot=self.condition.get_node_snapshot(self.condition_unique_id),
            true_subset=self.get_serializable_subset(),
            candidate_subset=get_serializable_candidate_subset(
                self._context.candidate_subset.convert_to_serializable_subset()
            ),
            subsets_with_metadata=self._subsets_with_metadata,
            start_timestamp=self._start_timestamp,
            end_timestamp=self._end_timestamp,
            child_evaluations=[
                child_result.serializable_evaluation for child_result in self._child_results
            ],
        )

    def set_internal_serializable_subset_override(self, override: SerializableEntitySubset) -> None:
        """Internal method for handling edge cases in which the serializable evaluation must be
        updated after evaluation completes.
        """
        self._serializable_subset_override = override

    def get_child_node_cursors(self) -> Mapping[str, AutomationConditionNodeCursor]:
        node_cursors = {self.condition_unique_id: self.node_cursor} if self.node_cursor else {}
        for child_result in self._child_results:
            node_cursors.update(child_result.get_child_node_cursors())
        return node_cursors

    def get_new_cursor(self) -> AutomationConditionCursor:
        return AutomationConditionCursor(
            previous_requested_subset=self.serializable_evaluation.true_subset,
            effective_timestamp=self._context.evaluation_time.timestamp(),
            last_event_id=self._context.max_storage_id,
            node_cursors_by_unique_id=self.get_child_node_cursors(),
            result_value_hash=self.value_hash,
        )

    def get_serializable_subset(self) -> SerializableEntitySubset:
        return (
            self.true_subset.convert_to_serializable_subset() or self._serializable_subset_override
        )

    def compute_legacy_expected_data_time(self) -> Optional[datetime.datetime]:
        from dagster._core.definitions.freshness_based_auto_materialize import (
            get_expected_data_time_for_asset_key,
        )

        legacy_context = self._context._legacy_context  # noqa
        if legacy_context:
            return get_expected_data_time_for_asset_key(
                legacy_context, will_materialize=not self.true_subset.is_empty
            )
        return None

    def pprint(self, indent=0) -> str:
        ret = f"AutomationResult(label={self.condition.name}, description={self.condition.description}, true={self.true_subset})"
        for child in self.child_results:
            nindent = indent + 4
            ret += f"\n{' '*nindent}{child.pprint(indent=nindent)}"
        return ret

    def __repr__(self) -> str:
        return self.pprint()


def _compute_subset_value_str(subset: SerializableEntitySubset) -> str:
    """Computes a unique string representing a given AssetSubsets. This string will be equal for
    equivalent AssetSubsets.
    """
    if isinstance(subset.value, bool):
        return str(subset.value)
    elif isinstance(subset.value, AllPartitionsSubset):
        return AllPartitionsSubset.__name__
    elif isinstance(subset.value, TimeWindowPartitionsSubset):
        return str(
            [
                (tw.start.timestamp(), tw.end.timestamp())
                for tw in sorted(subset.value.included_time_windows)
            ]
        )
    else:
        return str(list(sorted(subset.subset_value.get_partition_keys())))


def _compute_subset_with_metadata_value_str(subset_with_metadata: AssetSubsetWithMetadata):
    return _compute_subset_value_str(subset_with_metadata.subset) + str(
        sorted(subset_with_metadata.frozen_metadata)
    )
