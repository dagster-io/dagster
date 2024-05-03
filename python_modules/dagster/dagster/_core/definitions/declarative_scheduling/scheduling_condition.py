from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Sequence

from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionSnapshot,
)
from dagster._model import DagsterModel
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from .legacy.asset_condition import AssetConditionResult
    from .scheduling_context import SchedulingContext


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
    def evaluate(self, context: "SchedulingContext") -> "AssetConditionResult":
        raise NotImplementedError()

    def __and__(self, other: "SchedulingCondition") -> "SchedulingCondition":
        from .operators.boolean_operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "SchedulingCondition") -> "SchedulingCondition":
        from .operators.boolean_operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "SchedulingCondition":
        from .operators.boolean_operators import NotAssetCondition

        return NotAssetCondition(operand=self)
