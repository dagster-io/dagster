from enum import Enum
from typing import NamedTuple


class AutoMaterializeResultType(Enum):
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

    def __init__(self, id: str, result_type: AutoMaterializeResultType):
        self.id = id
        self.result_type = result_type

    # Materialization Conditions
    FRESHNESS = ("FRESHNESS", AutoMaterializeResultType.MATERIALIZE)
    DOWNSTREAM_FRESHNESS = ("DOWNSTREAM_FRESHNESS", AutoMaterializeResultType.MATERIALIZE)
    PARENT_MATERIALIZED = ("PARENT_MATERIALIZED", AutoMaterializeResultType.MATERIALIZE)
    MISSING = ("MISSING", AutoMaterializeResultType.MATERIALIZE)

    # Skip Conditions
    PARENT_OUTDATED = ("PARENT_OUTDATED", AutoMaterializeResultType.SKIP)

    # Discard Conditions


class AutoMaterializeConditionReason(NamedTuple):
    """A tuple which may contain specific information about why an asset was determined to meet a
    given auto-materialization condition.

    Currently, no additional information is provided for any condition.

    Should not be instantiated directly by the user.
    """

    condition: AutoMaterializeCondition

    @property
    def result_type(self) -> AutoMaterializeResultType:
        return self.condition.result_type

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
