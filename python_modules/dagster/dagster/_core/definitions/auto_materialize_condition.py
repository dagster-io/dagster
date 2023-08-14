from abc import ABC, abstractmethod, abstractproperty
from collections import defaultdict
from dataclasses import dataclass
import datetime
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
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from .asset_daemon_cursor import AssetDaemonCursor

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_based_auto_materialize import (
    freshness_conditions_for_asset_key,
)
from dagster._serdes import whitelist_for_serdes
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

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
    """Indicates that this asset should be materialized because one of its parents was materialized."""

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE
    updated_asset_keys: Optional[FrozenSet[AssetKey]] = None
    will_update_asset_keys: Optional[FrozenSet[AssetKey]] = None


@whitelist_for_serdes
class MissingAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be materialized because it is missing."""

    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class ParentOutdatedAutoMaterializeCondition(NamedTuple):
    """Indicates that this asset should be skipped because one or more of its parents are outdated."""

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


@dataclass
class RuleEvaluationContext:
    asset_key: AssetKey
    cursor: AssetDaemonCursor
    instance_queryer: CachingInstanceQueryer
    data_time_resolver: CachingDataTimeResolver
    will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    def materializable_in_same_run(self, child_key: AssetKey, parent_key: AssetKey) -> bool:
        """Returns whether a child asset can be materialized in the same run as a parent asset."""
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        return (
            # both assets must be materializable
            child_key in self.asset_graph.materializable_asset_keys
            and parent_key in self.asset_graph.materializable_asset_keys
            # the parent must have the same partitioning
            and self.asset_graph.have_same_partitioning(child_key, parent_key)
            # the parent must have a simple partition mapping to the child
            and (
                not self.asset_graph.is_partitioned(parent_key)
                or isinstance(
                    self.asset_graph.get_partition_mapping(child_key, parent_key),
                    (TimeWindowPartitionMapping, IdentityPartitionMapping),
                )
            )
            # the parent must be in the same repository to be materialized alongside the candidate
            and (
                not isinstance(self.asset_graph, ExternalAssetGraph)
                or self.asset_graph.get_repository_handle(child_key)
                == self.asset_graph.get_repository_handle(parent_key)
            )
        )


class MaterializeRuleEvaluationContext(RuleEvaluationContext):
    pass


@dataclass
class SkipRuleEvaluationContext(RuleEvaluationContext):
    candidates: AbstractSet[AssetKeyPartitionKey]

    @classmethod
    def from_materialize_context(
        cls,
        context: MaterializeRuleEvaluationContext,
        candidates: AbstractSet[AssetKeyPartitionKey],
    ) -> "SkipRuleEvaluationContext":
        return cls(
            asset_key=context.asset_key,
            cursor=context.cursor,
            instance_queryer=context.instance_queryer,
            data_time_resolver=context.data_time_resolver,
            will_materialize_mapping=context.will_materialize_mapping,
            expected_data_time_mapping=context.expected_data_time_mapping,
            candidates=candidates,
        )


class AutoMaterializeRule(ABC):
    decision_type: AutoMaterializeDecisionType

    @staticmethod
    def materialize_on_required_for_freshness() -> "MaterializeOnRequiredForFreshnessRule":
        return MaterializeOnRequiredForFreshnessRule()

    @staticmethod
    def materialize_on_parent_updated() -> "MaterializeOnParentUpdatedRule":
        return MaterializeOnParentUpdatedRule()

    @staticmethod
    def materialize_on_missing() -> "MaterializeOnMissingRule":
        return MaterializeOnMissingRule()

    @staticmethod
    def skip_on_parent_outdated() -> "SkipOnParentOutdatedRule":
        return SkipOnParentOutdatedRule()

    @abstractmethod
    def evaluate(
        self, context: RuleEvaluationContext
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        ...


class MaterializeOnRequiredForFreshnessRule(AutoMaterializeRule):
    decision_type = AutoMaterializeDecisionType.MATERIALIZE

    def evaluate(
        self, context: RuleEvaluationContext
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        (
            freshness_conditions,
            _,
            _,
        ) = freshness_conditions_for_asset_key(
            asset_key=context.asset_key,
            data_time_resolver=context.data_time_resolver,
            asset_graph=context.asset_graph,
            current_time=context.instance_queryer.evaluation_time,
            will_materialize_mapping=context.will_materialize_mapping,
            expected_data_time_mapping=context.expected_data_time_mapping,
        )
        return freshness_conditions


class MaterializeOnParentUpdatedRule(AutoMaterializeRule):
    def evaluate(
        self, context: RuleEvaluationContext
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        """Returns a mapping from ParentMaterializedAutoMaterializeCondition to the set of asset
        partitions that the condition applies to.
        """
        conditions = defaultdict(set)
        has_parents_that_will_update = set()

        # first, get the set of parents that will be materialized this tick, and see if we
        # can materialize this asset with those parents
        will_update_parents_by_asset_partition = defaultdict(set)
        for parent_key in context.asset_graph.get_parents(context.asset_key):
            if not context.materializable_in_same_run(context.asset_key, parent_key):
                continue
            for parent_partition in context.will_materialize_mapping.get(parent_key, set()):
                asset_partition = AssetKeyPartitionKey(
                    context.asset_key, parent_partition.partition_key
                )
                will_update_parents_by_asset_partition[asset_partition].add(parent_key)
                has_parents_that_will_update.add(asset_partition)

        # next, for each asset partition of this asset which has newly-updated parents, or
        # has a parent that will update, create a ParentMaterializedAutoMaterializeCondition
        has_or_will_update = (
            context.instance_queryer.get_asset_partitions_with_newly_updated_parents_for_key(
                context.asset_key
            )
            | has_parents_that_will_update
        )
        for asset_partition in has_or_will_update:
            parent_asset_partitions = context.asset_graph.get_parents_partitions(
                dynamic_partitions_store=context.instance_queryer,
                current_time=context.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions

            (
                updated_parent_asset_partitions,
                _,
            ) = context.instance_queryer.get_updated_and_missing_parent_asset_partitions(
                asset_partition,
                parent_asset_partitions,
                # do a precise check for updated parents, factoring in data versions, as long as
                # we're within reasonable limits on the number of partitions to check
                use_asset_versions=len(parent_asset_partitions | has_or_will_update) < 100,
            )
            updated_parents = {parent.asset_key for parent in updated_parent_asset_partitions}
            will_update_parents = will_update_parents_by_asset_partition[asset_partition]

            if updated_parents or will_update_parents:
                conditions[
                    ParentMaterializedAutoMaterializeCondition(
                        updated_asset_keys=frozenset(updated_parents),
                        will_update_asset_keys=frozenset(will_update_parents),
                    )
                ].add(asset_partition)
        return conditions


class MaterializeOnMissingRule(AutoMaterializeRule):
    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.MATERIALIZE

    def evaluate(
        self,
        context: RuleEvaluationContext,
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        """Returns a mapping from MissingAutoMaterializeCondition to the set of asset
        partitions that the condition applies to.
        """
        missing_asset_partitions = context.cursor.get_never_handled_root_asset_partitions_for_key(
            context.asset_key
        )
        # in addition to missing root asset partitions, check any asset partitions that we plan to
        # materialize to see if they are missing
        for candidate in (
            context.candidates
            | context.instance_queryer.get_asset_partitions_with_newly_updated_parents_for_key(
                context.asset_key
            )
        ):
            if not context.instance_queryer.asset_partition_has_materialization_or_observation(
                candidate
            ):
                missing_asset_partitions |= {candidate}
        return {MissingAutoMaterializeCondition(): missing_asset_partitions}


class SkipOnParentOutdatedRule(AutoMaterializeRule):
    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.SKIP

    def evaluate(
        self,
        context: SkipRuleEvaluationContext,
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        conditions = defaultdict(set)
        for candidate in context.candidates:
            unreconciled_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for parent in context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                context.asset_key,
                candidate.partition_key,
            ).parent_partitions:
                # parent will not be materialized this tick
                if parent not in context.will_materialize_mapping.get(
                    parent.asset_key, set()
                ) or not context.materializable_in_same_run(candidate.asset_key, parent.asset_key):
                    unreconciled_ancestors.update(
                        context.instance_queryer.get_root_unreconciled_ancestors(
                            asset_partition=parent
                        )
                    )
            if unreconciled_ancestors:
                conditions[
                    ParentOutdatedAutoMaterializeCondition(
                        waiting_on_asset_keys=frozenset(unreconciled_ancestors)
                    )
                ].update({candidate})
        return conditions
