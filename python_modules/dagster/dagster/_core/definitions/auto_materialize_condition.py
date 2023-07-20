from collections import defaultdict
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    FrozenSet,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._serdes import whitelist_for_serdes

from .asset_graph import AssetGraph
from .partition import (
    SerializedPartitionsSubset,
)

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


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

    @staticmethod
    def from_conditions(
        conditions: Optional[AbstractSet["AutoMaterializeCondition"]],
    ) -> Optional["AutoMaterializeDecisionType"]:
        """Based on a set of conditions, determine the resulting decision."""
        if not conditions:
            return None
        condition_decision_types = {condition.decision_type for condition in conditions}
        # precedence of decisions
        for decision_type in [
            AutoMaterializeDecisionType.SKIP,
            AutoMaterializeDecisionType.DISCARD,
            AutoMaterializeDecisionType.MATERIALIZE,
        ]:
            if decision_type in condition_decision_types:
                return decision_type
        return None


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
    updated_asset_keys: Optional[FrozenSet[AssetKey]] = None
    will_update_asset_keys: Optional[FrozenSet[AssetKey]] = None


@whitelist_for_serdes
class MissingAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because it is missing."""

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class ParentOutdatedAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be skipped because one or more of its parents are outdated.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.SKIP
    waiting_on_asset_keys: Optional[FrozenSet[AssetKey]] = None


@whitelist_for_serdes
class MaxMaterializationsExceededAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be discarded because materializing it would exceed the
    maximum number of materializations per minute.
    """

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.DISCARD


AutoMaterializeCondition: TypeAlias = Union[
    FreshnessAutoMaterializeCondition,
    DownstreamFreshnessAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
    MaxMaterializationsExceededAutoMaterializeCondition,
]


@whitelist_for_serdes
class AutoMaterializeAssetEvaluation(NamedTuple):
    """Represents the results of the auto-materialize logic for a single asset.

    Properties:
        asset_key (AssetKey): The asset key that was evaluated.
        partition_subsets_by_condition: The conditions that impact if the asset should be materialized, skipped, or
            discarded. If the asset is partitioned, this will be a list of tuples, where the first
            element is the condition and the second element is the serialized subset of partitions that the
            condition applies to. If it's not partitioned, the second element will be None.
    """

    asset_key: AssetKey
    partition_subsets_by_condition: Sequence[
        Tuple[AutoMaterializeCondition, Optional[SerializedPartitionsSubset]]
    ]
    num_requested: int
    num_skipped: int
    num_discarded: int
    run_ids: Set[str] = set()

    @staticmethod
    def from_conditions(
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        conditions_by_asset_partition: Mapping[
            AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]
        ],
        dynamic_partitions_store: "DynamicPartitionsStore",
    ) -> "AutoMaterializeAssetEvaluation":
        num_requested = 0
        num_skipped = 0
        num_discarded = 0

        for conditions in conditions_by_asset_partition.values():
            decision_type = AutoMaterializeDecisionType.from_conditions(conditions)
            if decision_type == AutoMaterializeDecisionType.MATERIALIZE:
                num_requested += 1
            elif decision_type == AutoMaterializeDecisionType.SKIP:
                num_skipped += 1
            elif decision_type == AutoMaterializeDecisionType.DISCARD:
                num_discarded += 1

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if partitions_def is None:
            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (condition, None)
                    for condition in set().union(*conditions_by_asset_partition.values())
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
            )
        else:
            partition_keys_by_condition = defaultdict(set)

            for asset_partition, conditions in conditions_by_asset_partition.items():
                for condition in conditions:
                    partition_keys_by_condition[condition].add(
                        check.not_none(asset_partition.partition_key)
                    )

            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (
                        condition,
                        SerializedPartitionsSubset.from_subset(
                            subset=partitions_def.empty_subset().with_partition_keys(
                                partition_keys
                            ),
                            partitions_def=partitions_def,
                            dynamic_partitions_store=dynamic_partitions_store,
                        ),
                    )
                    for condition, partition_keys in partition_keys_by_condition.items()
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
            )
