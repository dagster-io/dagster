from enum import Enum
from typing import NamedTuple


class AutoMaterializeResult(Enum):
    """Represents the set of results of the auto-materialize logic.

    MATERIALIZE: The asset should be materialized by a run kicked off on this tick
    SKIP: The asset should not be materialized by a run kicked off on this tick, because future
        ticks are expected to materialize it.
    DISCARD: The asset should not be materialized by a run kicked off on this tick, but future
        ticks are not expected to materialize it.
    """

    MATERIALIZE = "MATERIALIZE"
    SKIP = "SKIP"
    DISCARD = "DISCARD"


class AutoMaterializeCondition(Enum):
    """Represents the set of conditions that can impact auto-materialization for an asset."""

    def __init__(self, id: str, result: AutoMaterializeResult):
        self.id = id
        self.result = result

    # Materialization Reasons
    FRESHNESS = ("FRESHNESS", AutoMaterializeResult.MATERIALIZE)
    DOWNSTREAM_FRESHNESS = ("DOWNSTREAM_FRESHNESS", AutoMaterializeResult.MATERIALIZE)
    PARENT_MATERIALIZED = ("PARENT_MATERIALIZED", AutoMaterializeResult.MATERIALIZE)
    MISSING = ("MISSING", AutoMaterializeResult.MATERIALIZE)

    # Skip Reasons
    PARENT_OUTDATED = ("PARENT_OUTDATED", AutoMaterializeResult.SKIP)

    # Discard Reasons


class AutoMaterializeConditionReason(NamedTuple):
    """Denotes the reason that the auto-materialize logic decided that an asset should be materialized.

    In the future, may be extended to support additional details attached to raw condition.

    Should not be instantiated directly by the user.
    """

    condition: AutoMaterializeCondition

    @property
    def result(self) -> AutoMaterializeResult:
        return self.condition.result

    @staticmethod
    def freshness() -> "AutoMaterializeConditionReason":
        return AutoMaterializeConditionReason(condition=AutoMaterializeCondition.FRESHNESS)

    @staticmethod
    def downstream_freshness() -> "AutoMaterializeConditionReason":
        return AutoMaterializeConditionReason(
            condition=AutoMaterializeCondition.DOWNSTREAM_FRESHNESS
        )

    @staticmethod
    def parent_materialized() -> "AutoMaterializeConditionReason":
        return AutoMaterializeConditionReason(
            condition=AutoMaterializeCondition.PARENT_MATERIALIZED
        )

    @staticmethod
    def missing() -> "AutoMaterializeConditionReason":
        return AutoMaterializeConditionReason(condition=AutoMaterializeCondition.MISSING)

    @staticmethod
    def parent_outdated() -> "AutoMaterializeConditionReason":
        return AutoMaterializeConditionReason(condition=AutoMaterializeCondition.PARENT_OUTDATED)
