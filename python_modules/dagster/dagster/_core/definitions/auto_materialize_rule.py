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
from .auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)

from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_based_auto_materialize import (
    freshness_conditions_for_asset_key,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .asset_graph import AssetGraph

if TYPE_CHECKING:
    from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
    from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor


class RuleEvaluationContext(NamedTuple):
    asset_key: AssetKey
    cursor: "AssetDaemonCursor"
    instance_queryer: CachingInstanceQueryer
    data_time_resolver: CachingDataTimeResolver
    will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]
    candidates: AbstractSet[AssetKeyPartitionKey]
    daemon_context: "AssetDaemonContext"

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

    def non_materializing_parents(
        self, asset_partition: AssetKeyPartitionKey
    ) -> Set[AssetKeyPartitionKey]:
        """Returns the set of parent asset partitions that will not materialize with this asset partition."""
        return {
            parent
            for parent in self.asset_graph.get_parents_partitions(
                dynamic_partitions_store=self.instance_queryer,
                current_time=self.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions
            if parent not in self.will_materialize_mapping.get(parent.asset_key, set())
            or not self.materializable_in_same_run(asset_partition.asset_key, parent.asset_key)
        }


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
        freshness_conditions = freshness_conditions_for_asset_key(
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
            context.daemon_context.get_asset_partitions_with_newly_updated_parents_for_key(
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

            updated_parent_asset_partitions = context.instance_queryer.get_updated_parent_asset_partitions(
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
        missing_asset_partitions = (
            context.daemon_context.get_never_handled_root_asset_partitions_for_key(
                context.asset_key
            )
        )
        # in addition to missing root asset partitions, check any asset partitions with updated
        # parents to see if they're missing
        for (
            candidate
        ) in context.daemon_context.get_asset_partitions_with_newly_updated_parents_for_key(
            context.asset_key
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
        context: RuleEvaluationContext,
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        conditions = defaultdict(set)
        for candidate in context.candidates:
            unreconciled_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for parent in context.non_materializing_parents(candidate):
                unreconciled_ancestors.update(
                    context.instance_queryer.get_root_unreconciled_ancestors(asset_partition=parent)
                )
            if unreconciled_ancestors:
                conditions[
                    ParentOutdatedAutoMaterializeCondition(
                        waiting_on_asset_keys=frozenset(unreconciled_ancestors)
                    )
                ].update({candidate})
        return conditions


class SkipOnParentMissingRule(AutoMaterializeRule):
    decision_type: AutoMaterializeDecisionType = AutoMaterializeDecisionType.SKIP

    def evaluate(
        self,
        context: RuleEvaluationContext,
    ) -> Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        conditions = defaultdict(set)
        for candidate in context.candidates:
            missing_parent_asset_keys = set()
            for parent in context.non_materializing_parents(candidate):
                if not context.instance_queryer.asset_partition_has_materialization_or_observation(
                    parent
                ):
                    missing_parent_asset_keys.add(parent.asset_key)
            if missing_parent_asset_keys:
                conditions[
                    ParentOutdatedAutoMaterializeCondition(
                        waiting_on_asset_keys=frozenset(missing_parent_asset_keys)
                    )
                ].update({candidate})
        return conditions
