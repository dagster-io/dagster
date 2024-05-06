import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Sequence

import pendulum

from dagster._annotations import experimental
from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
)
from dagster._model import DagsterModel
from dagster._serdes.serdes import PackableValue
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from .operands import (
        InLatestTimeWindowCondition,
        InProgressSchedulingCondition,
        MissingSchedulingCondition,
    )
    from .operators import (
        AllDepsCondition,
        AndAssetCondition,
        AnyDepsCondition,
        NotAssetCondition,
        OrAssetCondition,
    )
    from .scheduling_context import SchedulingContext


@experimental
class SchedulingCondition(ABC, DagsterModel):
    @property
    def children(self) -> Sequence["SchedulingCondition"]:
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def get_snapshot(self, unique_id: str) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
        )

    def get_unique_id(self, parent_unique_id: Optional[str]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @abstractmethod
    def evaluate(self, context: "SchedulingContext") -> "SchedulingResult":
        raise NotImplementedError()

    def __and__(self, other: "SchedulingCondition") -> "AndAssetCondition":
        from .operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "SchedulingCondition") -> "OrAssetCondition":
        from .operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "NotAssetCondition":
        from .operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    @staticmethod
    def any_deps_match(condition: "SchedulingCondition") -> "AnyDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.
        """
        from .operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @staticmethod
    def all_deps_match(condition: "SchedulingCondition") -> "AllDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.
        """
        from .operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @staticmethod
    def missing() -> "MissingSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has never been
        materialized or observed.
        """
        from .operands import MissingSchedulingCondition

        return MissingSchedulingCondition()

    @staticmethod
    def in_progress() -> "InProgressSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it is part of an in-progress run."""
        from .operands import InProgressSchedulingCondition

        return InProgressSchedulingCondition()

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "InLatestTimeWindowCondition":
        """Returns a SchedulingCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if this is used on a daily-partitioned asset with a lookback_delta of
                48 hours, this will return the latest two partitions.
        """
        from .operands import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition(
            lookback_seconds=lookback_delta.total_seconds() if lookback_delta else None
        )


class SchedulingResult(DagsterModel):
    condition: SchedulingCondition
    condition_unique_id: str
    start_timestamp: float
    end_timestamp: float

    true_slice: AssetSlice
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    extra_state: Any
    child_results: Sequence["SchedulingResult"]

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

    @staticmethod
    def create_from_children(
        context: "SchedulingContext",
        true_slice: AssetSlice,
        child_results: Sequence["SchedulingResult"],
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return SchedulingResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.create_time.timestamp(),
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=true_slice,
            candidate_subset=context.candidate_slice.convert_to_valid_asset_subset(),
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
        )

    @staticmethod
    def create(
        context: "SchedulingContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: PackableValue = None,
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return SchedulingResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.create_time.timestamp(),
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=true_slice,
            candidate_subset=context.candidate_slice.convert_to_valid_asset_subset(),
            subsets_with_metadata=subsets_with_metadata,
            child_results=[],
            extra_state=extra_state,
        )
