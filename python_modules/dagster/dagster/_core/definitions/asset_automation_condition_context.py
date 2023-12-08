import datetime
import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, AbstractSet, Mapping, Optional, Sequence

from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .asset_daemon_cursor import AssetDaemonAssetCursor
from .asset_graph import AssetGraph
from .asset_subset import AssetSubset

if TYPE_CHECKING:
    from dagster._core.definitions.asset_automation_evaluator import AssetSubsetWithMetdata

    from .asset_automation_evaluator import AutomationCondition, ConditionEvaluation
    from .asset_daemon_context import AssetDaemonContext


@dataclass(frozen=True)
class AssetAutomationEvaluationContext:
    """Context object containing methods and properties used for evaluating the entire state of an
    asset's automation rules.
    """

    asset_key: AssetKey
    asset_cursor: Optional[AssetDaemonAssetCursor]
    root_condition: "AutomationCondition"

    instance_queryer: CachingInstanceQueryer
    data_time_resolver: CachingDataTimeResolver
    daemon_context: "AssetDaemonContext"

    evaluation_results_by_key: Mapping[AssetKey, "ConditionEvaluation"]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.asset_graph.get_partitions_def(self.asset_key)

    @property
    def evaluation_time(self) -> datetime.datetime:
        """Returns the time at which this rule is being evaluated."""
        return self.instance_queryer.evaluation_time

    @functools.cached_property
    def latest_evaluation(self) -> Optional["ConditionEvaluation"]:
        if not self.asset_cursor:
            return None
        return self.asset_cursor.latest_evaluation

    @functools.cached_property
    def parent_will_update_subset(self) -> AssetSubset:
        """Returns the set of asset partitions whose parents will be updated on this tick, and which
        can be materialized in the same run as this asset.
        """
        subset = self.empty_subset()
        for parent_key in self.asset_graph.get_parents(self.asset_key):
            if not self.materializable_in_same_run(self.asset_key, parent_key):
                continue
            parent_result = self.evaluation_results_by_key.get(parent_key)
            if not parent_result:
                continue
            parent_subset = parent_result.true_subset
            subset |= parent_subset._replace(asset_key=self.asset_key)
        return subset

    @property
    def previous_tick_requested_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were requested on the previous tick."""
        if not self.latest_evaluation:
            return self.empty_subset()
        return self.latest_evaluation.true_subset

    @functools.cached_property
    def materialized_since_previous_tick_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return AssetSubset.from_asset_partitions_set(
            self.asset_key,
            self.partitions_def,
            self.instance_queryer.get_asset_partitions_updated_after_cursor(
                self.asset_key,
                asset_partitions=None,
                after_cursor=self.asset_cursor.latest_storage_id if self.asset_cursor else None,
                respect_materialization_data_versions=False,
            ),
        )

    @functools.cached_property
    def materialized_requested_or_discarded_since_previous_tick_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        if not self.latest_evaluation:
            return self.materialized_since_previous_tick_subset
        return (
            self.materialized_since_previous_tick_subset
            | self.latest_evaluation.true_subset
            | (self.latest_evaluation.discard_subset(self.root_condition) or self.empty_subset())
        )

    @functools.cached_property
    def never_materialized_requested_or_discarded_root_subset(self) -> AssetSubset:
        if self.asset_key not in self.asset_graph.root_materializable_or_observable_asset_keys:
            return self.empty_subset()

        handled_subset = (
            self.asset_cursor.materialized_requested_or_discarded_subset
            if self.asset_cursor
            else self.empty_subset()
        )
        unhandled_subset = handled_subset.inverse(
            self.partitions_def,
            dynamic_partitions_store=self.instance_queryer,
            current_time=self.evaluation_time,
        )
        return unhandled_subset - self.materialized_since_previous_tick_subset

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

    def get_parents_that_will_not_be_materialized_on_current_tick(
        self, *, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of parent asset partitions that will not be updated in the same run of
        this asset partition if a run is launched for this asset partition on this tick.
        """
        return {
            parent
            for parent in self.asset_graph.get_parents_partitions(
                dynamic_partitions_store=self.instance_queryer,
                current_time=self.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions
            if not self.will_update_asset_partition(parent)
            or not self.materializable_in_same_run(asset_partition.asset_key, parent.asset_key)
        }

    def will_update_asset_partition(self, asset_partition: AssetKeyPartitionKey) -> bool:
        parent_evaluation = self.evaluation_results_by_key.get(asset_partition.asset_key)
        if not parent_evaluation:
            return False
        return asset_partition in parent_evaluation.true_subset

    def empty_subset(self) -> AssetSubset:
        return AssetSubset.empty(self.asset_key, self.partitions_def)

    def get_root_condition_context(self) -> "AssetAutomationConditionEvaluationContext":
        return AssetAutomationConditionEvaluationContext(
            asset_context=self,
            condition=self.root_condition,
            candidate_subset=AssetSubset.all(
                asset_key=self.asset_key,
                partitions_def=self.partitions_def,
                dynamic_partitions_store=self.instance_queryer,
                current_time=self.instance_queryer.evaluation_time,
            ),
            latest_evaluation=self.latest_evaluation,
        )

    def get_new_asset_cursor(self, evaluation: "ConditionEvaluation") -> AssetDaemonAssetCursor:
        """Returns a new AssetDaemonAssetCursor based on the current cursor and the results of
        this tick's evaluation.
        """
        previous_handled_subset = (
            self.asset_cursor.materialized_requested_or_discarded_subset
            if self.asset_cursor
            else self.empty_subset()
        )
        new_handled_subset = (
            previous_handled_subset
            | self.materialized_requested_or_discarded_since_previous_tick_subset
            | evaluation.true_subset
            | (evaluation.discard_subset(self.root_condition) or self.empty_subset())
        )
        return AssetDaemonAssetCursor(
            asset_key=self.asset_key,
            latest_storage_id=self.daemon_context.get_new_latest_storage_id(),
            latest_evaluation=evaluation,
            latest_evaluation_timestamp=self.evaluation_time.timestamp(),
            materialized_requested_or_discarded_subset=new_handled_subset,
        )


@dataclass(frozen=True)
class AssetAutomationConditionEvaluationContext:
    """Context object containing methods and properties used for evaluating a particular AutomationCondition."""

    asset_context: AssetAutomationEvaluationContext
    condition: "AutomationCondition"
    candidate_subset: AssetSubset
    latest_evaluation: Optional["ConditionEvaluation"]

    @property
    def asset_key(self) -> AssetKey:
        return self.asset_context.asset_key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.asset_context.partitions_def

    @property
    def asset_cursor(self) -> Optional[AssetDaemonAssetCursor]:
        return self.asset_context.asset_cursor

    @property
    def asset_graph(self) -> AssetGraph:
        return self.asset_context.asset_graph

    @property
    def instance_queryer(self) -> CachingInstanceQueryer:
        return self.asset_context.instance_queryer

    @property
    def max_storage_id(self) -> Optional[int]:
        return self.asset_cursor.latest_storage_id if self.asset_cursor else None

    @property
    def latest_evaluation_timestamp(self) -> Optional[float]:
        return self.asset_cursor.latest_evaluation_timestamp if self.asset_cursor else None

    @property
    def previous_tick_true_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were true on the previous tick."""
        if not self.latest_evaluation:
            return self.empty_subset()
        return self.latest_evaluation.true_subset

    @property
    def parent_has_updated_subset(self) -> AssetSubset:
        """Returns the set of asset partitions whose parents have updated since the last time this
        condition was evaluated.
        """
        return AssetSubset.from_asset_partitions_set(
            self.asset_key,
            self.partitions_def,
            self.asset_context.instance_queryer.asset_partitions_with_newly_updated_parents(
                latest_storage_id=self.max_storage_id,
                child_asset_key=self.asset_context.asset_key,
                map_old_time_partitions=False,
            ),
        )

    @property
    def candidate_parent_has_or_will_update_subset(self) -> AssetSubset:
        """Returns the set of candidates for this tick which have parents that have updated since
        the previous tick, or will update on this tick.
        """
        return self.candidate_subset & (
            self.parent_has_updated_subset | self.asset_context.parent_will_update_subset
        )

    @property
    def candidates_not_evaluated_on_previous_tick_subset(self) -> AssetSubset:
        """Returns the set of candidates for this tick which were not candidates on the previous
        tick.
        """
        if not self.latest_evaluation:
            return self.candidate_subset
        return self.candidate_subset - self.latest_evaluation.candidate_subset

    @property
    def materialized_since_previous_tick_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return self.asset_context.materialized_since_previous_tick_subset

    @property
    def materialized_requested_or_discarded_since_previous_tick_subset(self) -> AssetSubset:
        """Returns the set of asset partitions that were materialized since the previous tick."""
        return self.asset_context.materialized_requested_or_discarded_since_previous_tick_subset

    @property
    def previous_tick_subsets_with_metadata(self) -> Sequence["AssetSubsetWithMetdata"]:
        """Returns the RuleEvaluationResults calculated on the previous tick for this condition."""
        return self.latest_evaluation.subsets_with_metadata if self.latest_evaluation else []

    def empty_subset(self) -> AssetSubset:
        return self.asset_context.empty_subset()

    def for_child(
        self, condition: "AutomationCondition", candidate_subset: AssetSubset
    ) -> "AssetAutomationConditionEvaluationContext":
        return AssetAutomationConditionEvaluationContext(
            asset_context=self.asset_context,
            condition=condition,
            candidate_subset=candidate_subset,
            latest_evaluation=self.latest_evaluation.for_child(condition)
            if self.latest_evaluation
            else None,
        )
