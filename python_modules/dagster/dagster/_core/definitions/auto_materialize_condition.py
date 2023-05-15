from enum import Enum
from typing import NamedTuple, Union

from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class AutoMaterializeDecisionType(Enum):
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


@whitelist_for_serdes
class FreshnessAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because it requires newer data in order to
    align with its freshness policy.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class DownstreamFreshnessAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because one of its downstream assets
    requires newer data in order to align with its freshness policy.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class ParentMaterializedAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because one of its parents was materialized.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class MissingAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because it is missing."""

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class ParentOutdatedAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be skipped because one or more of its parents are outdated.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.SKIP


@whitelist_for_serdes
class MaxMaterializationsExceededAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be discarded because materializing it would exceed the
    maximum number of materializations per minute.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.DISCARD


AutoMaterializeCondition = Union[
    FreshnessAutoMaterializeCondition,
    DownstreamFreshnessAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
    MaxMaterializationsExceededAutoMaterializeCondition,
]
