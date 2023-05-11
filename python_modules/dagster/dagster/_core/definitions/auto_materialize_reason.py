from enum import Enum
from typing import NamedTuple, Union

from dagster._serdes import whitelist_for_serdes


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


@whitelist_for_serdes
class FreshnessAutoMaterializeReason(NamedTuple):
    """Indicates that this asset should be materialized because it requires newer data in order to
    align with its freshness policy.
    """

    result_type: AutoMaterializeResultType = AutoMaterializeResultType.MATERIALIZE


@whitelist_for_serdes
class DownstreamFreshnessAutoMaterializeReason(NamedTuple):
    """Indicates that this asset should be materialized because one of its downstream assets
    requires newer data in order to align with its freshness policy.
    """

    result_type: AutoMaterializeResultType = AutoMaterializeResultType.MATERIALIZE


@whitelist_for_serdes
class ParentMaterializedAutoMaterializeReason(NamedTuple):
    """Indicates that this asset should be materialized because one of its parents was materialized.
    """

    result_type: AutoMaterializeResultType = AutoMaterializeResultType.MATERIALIZE


@whitelist_for_serdes
class MissingAutoMaterializeReason(NamedTuple):
    """Indicates that this asset should be materialized because it is missing."""

    result_type: AutoMaterializeResultType = AutoMaterializeResultType.MATERIALIZE


@whitelist_for_serdes
class ParentOutdatedAutoMaterializeReason(NamedTuple):
    """Indicates that this asset should be skipped because one or more of its parents are outdated.
    """

    result_type: AutoMaterializeResultType = AutoMaterializeResultType.SKIP


AutoMaterializeReason = Union[
    FreshnessAutoMaterializeReason,
    DownstreamFreshnessAutoMaterializeReason,
    ParentMaterializedAutoMaterializeReason,
    MissingAutoMaterializeReason,
    ParentOutdatedAutoMaterializeReason,
]
