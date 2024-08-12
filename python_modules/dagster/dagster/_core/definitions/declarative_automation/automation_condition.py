import datetime
from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionCursor,
    AutomationConditionEvaluation,
    AutomationConditionNodeCursor,
    AutomationConditionSnapshot,
    get_serializable_candidate_subset,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._record import copy
from dagster._serdes.serdes import is_whitelisted_for_serdes_object
from dagster._time import get_current_timestamp
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

    from .automation_context import AutomationContext
    from .operands import (
        CodeVersionChangedCondition,
        CronTickPassedCondition,
        FailedAutomationCondition,
        InLatestTimeWindowCondition,
        InProgressAutomationCondition,
        MissingAutomationCondition,
        NewlyRequestedCondition,
        NewlyUpdatedCondition,
        WillBeRequestedCondition,
    )
    from .operators import (
        AllDepsCondition,
        AndAutomationCondition,
        AnyDepsCondition,
        AnyDownstreamConditionsCondition,
        NewlyTrueCondition,
        NotAutomationCondition,
        OrAutomationCondition,
        SinceCondition,
    )


class AutomationCondition(ABC):
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
        return False

    @property
    def children(self) -> Sequence["AutomationCondition"]:
        return []

    @property
    def description(self) -> str:
        """Human-readable description of when this condition is true."""
        return ""

    @property
    def label(self) -> Optional[str]:
        """User-provided label subjectively describing the purpose of this condition in the broader evaluation tree."""
        return None

    @property
    def name(self) -> str:
        """Formal name of this specific condition, generally aligning with its static constructor."""
        return self.__class__.__name__

    def get_snapshot(self, unique_id: str) -> AutomationConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AutomationConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
            label=self.label,
            name=self.name,
        )

    def get_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), str(index), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    def get_hash(
        self, *, parent_unique_id: Optional[str] = None, index: Optional[int] = None
    ) -> int:
        """Generates a hash based off of the unique ids of all children."""
        unique_id = self.get_unique_id(parent_unique_id=parent_unique_id, index=index)
        hashes = [hash(unique_id)]
        for i, child in enumerate(self.children):
            hashes.append(child.get_hash(parent_unique_id=unique_id, index=i))
        return hash(tuple(hashes))

    def __hash__(self) -> int:
        return self.get_hash()

    @property
    def has_rule_condition(self) -> bool:
        from .legacy import RuleCondition

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
    def evaluate(self, context: "AutomationContext") -> "AutomationResult":
        raise NotImplementedError()

    def __and__(self, other: "AutomationCondition") -> "AndAutomationCondition":
        from .operators import AndAutomationCondition

        # group AndAutomationConditions together
        if isinstance(self, AndAutomationCondition):
            return AndAutomationCondition(operands=[*self.operands, other])
        return AndAutomationCondition(operands=[self, other])

    def __or__(self, other: "AutomationCondition") -> "OrAutomationCondition":
        from .operators import OrAutomationCondition

        # group OrAutomationConditions together
        if isinstance(self, OrAutomationCondition):
            return OrAutomationCondition(operands=[*self.operands, other])
        return OrAutomationCondition(operands=[self, other])

    def __invert__(self) -> "NotAutomationCondition":
        from .operators import NotAutomationCondition

        return NotAutomationCondition(operand=self)

    @public
    def with_label(self, label: Optional[str]) -> "AutomationCondition":
        """Returns a copy of this AutomationCondition with a human-readable label."""
        return copy(self, label=label)

    def since(self, reset_condition: "AutomationCondition") -> "SinceCondition":
        """Returns a AutomationCondition that is true if this condition has become true since the
        last time the reference condition became true.
        """
        from .operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=reset_condition)

    def newly_true(self) -> "NewlyTrueCondition":
        """Returns a AutomationCondition that is true only on the tick that this condition goes
        from false to true for a given asset partition.
        """
        from .operators import NewlyTrueCondition

        return NewlyTrueCondition(operand=self)

    @public
    @experimental
    @staticmethod
    def any_deps_match(condition: "AutomationCondition") -> "AnyDepsCondition":
        """Returns a AutomationCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's dependencies.
        """
        from .operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @public
    @experimental
    @staticmethod
    def all_deps_match(condition: "AutomationCondition") -> "AllDepsCondition":
        """Returns a AutomationCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's dependencies.
        """
        from .operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @public
    @experimental
    @staticmethod
    def missing() -> "MissingAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if it has never been
        materialized or observed.
        """
        from .operands import MissingAutomationCondition

        return MissingAutomationCondition()

    @public
    @experimental
    @staticmethod
    def in_progress() -> "InProgressAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if it is part of an in-progress run."""
        from .operands import InProgressAutomationCondition

        return InProgressAutomationCondition()

    @public
    @experimental
    @staticmethod
    def failed() -> "FailedAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if its latest run failed."""
        from .operands import FailedAutomationCondition

        return FailedAutomationCondition()

    @public
    @experimental
    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "InLatestTimeWindowCondition":
        """Returns a AutomationCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if this is used on a daily-partitioned asset with a lookback_delta of
                48 hours, this will return the latest two partitions.
        """
        from .operands import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition.from_lookback_delta(lookback_delta)

    @public
    @experimental
    @staticmethod
    def will_be_requested() -> "WillBeRequestedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it will be requested this tick."""
        from .operands import WillBeRequestedCondition

        return WillBeRequestedCondition()

    @public
    @experimental
    @staticmethod
    def newly_updated() -> "NewlyUpdatedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it has been updated since the previous tick."""
        from .operands import NewlyUpdatedCondition

        return NewlyUpdatedCondition()

    @public
    @experimental
    @staticmethod
    def newly_requested() -> "NewlyRequestedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it was requested on the previous tick."""
        from .operands import NewlyRequestedCondition

        return NewlyRequestedCondition()

    @public
    @experimental
    @staticmethod
    def code_version_changed() -> "CodeVersionChangedCondition":
        """Returns a AutomationCondition that is true for an asset partition if its asset's code
        version has been changed since the previous tick.
        """
        from .operands import CodeVersionChangedCondition

        return CodeVersionChangedCondition()

    @public
    @experimental
    @staticmethod
    def cron_tick_passed(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "CronTickPassedCondition":
        """Returns a AutomationCondition that is true for all asset partitions whenever a cron tick of the provided schedule is passed."""
        from .operands import CronTickPassedCondition

        return CronTickPassedCondition(cron_schedule=cron_schedule, cron_timezone=cron_timezone)

    @public
    @experimental
    @staticmethod
    def eager() -> "AutomationCondition":
        """Returns a condition which will "eagerly" fill in missing partitions as they are created,
        and ensures unpartitioned assets are updated whenever their dependencies are updated (either
        via scheduled execution or ad-hoc runs).

        Specifically, this is a composite AutomationCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - At least one of its parents has been updated more recently than it has been requested, or
            the asset partition has never been materialized
        - None of its parent partitions are missing
        - None of its parent partitions are currently part of an in-progress run
        """
        with disable_dagster_warnings():
            became_missing_or_any_parents_updated = (
                AutomationCondition.missing().newly_true().with_label("became missing")
                | AutomationCondition.any_deps_match(
                    AutomationCondition.newly_updated() | AutomationCondition.will_be_requested()
                ).with_label("any parents updated")
            )

            any_parents_missing = AutomationCondition.any_deps_match(
                AutomationCondition.missing() & ~AutomationCondition.will_be_requested()
            ).with_label("any parents missing")
            any_parents_in_progress = AutomationCondition.any_deps_match(
                AutomationCondition.in_progress()
            ).with_label("any parents in progress")
            return (
                AutomationCondition.in_latest_time_window()
                & became_missing_or_any_parents_updated.since(
                    AutomationCondition.newly_requested() | AutomationCondition.newly_updated()
                )
                & ~any_parents_missing
                & ~any_parents_in_progress
                & ~AutomationCondition.in_progress()
            ).with_label("eager")

    @public
    @experimental
    @staticmethod
    def on_cron(cron_schedule: str, cron_timezone: str = "UTC") -> "AutomationCondition":
        """Returns a condition which will materialize asset partitions within the latest time window
        on a given cron schedule, after their parents have been updated. For example, if the
        cron_schedule is set to "`0 0 * * *`" (every day at midnight), then this rule will not become
        true on a given day until all of its parents have been updated during that same day.

        Specifically, this is a composite AutomationCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - All parent asset partitions have been updated since the latest tick of the provided cron
            schedule, or will be requested this tick
        - The asset partition has not been requested since the latest tick of the provided cron schedule
        """
        with disable_dagster_warnings():
            cron_label = f"'{cron_schedule}' ({cron_timezone})"
            cron_tick_passed = AutomationCondition.cron_tick_passed(
                cron_schedule, cron_timezone
            ).with_label(f"tick of {cron_label} passed")
            all_deps_updated_since_cron = AutomationCondition.all_deps_match(
                AutomationCondition.newly_updated().since(cron_tick_passed)
                | AutomationCondition.will_be_requested()
            ).with_label(f"all parents updated since {cron_label}")
            return (
                AutomationCondition.in_latest_time_window()
                & cron_tick_passed.since(AutomationCondition.newly_requested())
                & all_deps_updated_since_cron
            ).with_label(f"on cron {cron_label}")

    @public
    @experimental
    @staticmethod
    def any_downstream_conditions() -> "AnyDownstreamConditionsCondition":
        """Returns a condition which will represent the union of all distinct downstream conditions."""
        from .operators import AnyDownstreamConditionsCondition

        return AnyDownstreamConditionsCondition()


class AutomationResult:
    """The result of evaluating an AutomationCondition."""

    def __init__(
        self,
        context: "AutomationContext",
        true_slice: AssetSlice,
        cursor: Optional[str] = None,
        child_results: Optional[Sequence["AutomationResult"]] = None,
        **kwargs,
    ):
        from dagster._core.definitions.declarative_automation.automation_context import (
            AutomationContext,
        )

        self._context = check.inst_param(context, "context", AutomationContext)
        self._true_slice = check.inst_param(true_slice, "true_slice", AssetSlice)
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
        self._serializable_evaluation_override: Optional[AutomationConditionEvaluation] = None

    @property
    def asset_key(self) -> AssetKey:
        return self._true_slice.asset_key

    @property
    def true_slice(self) -> AssetSlice:
        return self._true_slice

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

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
            _compute_subset_value_str(self.true_subset),
            _compute_subset_value_str(
                self._context.candidate_slice.convert_to_valid_asset_subset()
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
            true_subset=self.true_subset,
            candidate_subset=get_serializable_candidate_subset(
                self._context.candidate_slice.convert_to_valid_asset_subset()
            ),
            subsets_with_metadata=self._subsets_with_metadata,
            extra_state=self._extra_state,
        )

    @cached_property
    def _serializable_evaluation(self) -> AutomationConditionEvaluation:
        return AutomationConditionEvaluation(
            condition_snapshot=self.condition.get_snapshot(self.condition_unique_id),
            true_subset=self.true_subset,
            candidate_subset=get_serializable_candidate_subset(
                self._context.candidate_slice.convert_to_valid_asset_subset()
            ),
            subsets_with_metadata=self._subsets_with_metadata,
            start_timestamp=self._start_timestamp,
            end_timestamp=self._end_timestamp,
            child_evaluations=[
                child_result.serializable_evaluation for child_result in self._child_results
            ],
        )

    @property
    def serializable_evaluation(self) -> AutomationConditionEvaluation:
        """Serializable representation of the evaluation of this condition."""
        return self._serializable_evaluation_override or self._serializable_evaluation

    def set_internal_serializable_evaluation_override(
        self, override: AutomationConditionEvaluation
    ) -> None:
        """Internal method for handling edge cases in which the serializable evaluation must be
        updated after evaluation completes.
        """
        self._serializable_evaluation_override = override

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


def _compute_subset_value_str(subset: AssetSubset) -> str:
    """Computes a unique string representing a given AssetSubsets. This string will be equal for
    equivalent AssetSubsets.
    """
    if isinstance(subset.value, bool):
        return str(subset.value)
    elif isinstance(subset.value, AllPartitionsSubset):
        return AllPartitionsSubset.__name__
    elif isinstance(subset.value, BaseTimeWindowPartitionsSubset):
        return str(
            [
                (tw.start.timestamp(), tw.end.timestamp())
                for tw in sorted(subset.value.included_time_windows)
            ]
        )
    else:
        return str(list(sorted(subset.asset_partitions)))


def _compute_subset_with_metadata_value_str(subset_with_metadata: AssetSubsetWithMetadata):
    return _compute_subset_value_str(subset_with_metadata.subset) + str(
        sorted(subset_with_metadata.frozen_metadata)
    )
