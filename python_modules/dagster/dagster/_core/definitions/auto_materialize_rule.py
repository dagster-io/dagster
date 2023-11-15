import datetime
import functools
from abc import ABC, abstractmethod, abstractproperty
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
)

import pytz

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeDecisionType,
    AutoMaterializeRuleEvaluationData,
    AutoMaterializeRuleSnapshot,
    ParentUpdatedRuleEvaluationData,
    RuleEvaluationResults,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_based_auto_materialize import (
    freshness_evaluation_results_for_asset_key,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import get_time_partitions_def
from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.storage.tags import AUTO_MATERIALIZE_TAG
from dagster._serdes.serdes import (
    whitelist_for_serdes,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster._utils.schedules import (
    cron_string_iterator,
    is_valid_cron_string,
    reverse_cron_string_iterator,
)

from .asset_graph import AssetGraph, sort_key_for_asset_partition

if TYPE_CHECKING:
    from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
    from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
    from dagster._core.definitions.auto_materialize_rule_evaluation import (
        AutoMaterializeAssetEvaluation,
    )


@dataclass(frozen=True)
class RuleEvaluationContext:
    asset_key: AssetKey
    cursor: "AssetDaemonCursor"
    instance_queryer: CachingInstanceQueryer
    data_time_resolver: CachingDataTimeResolver
    # Tracks which asset partitions are already slated for materialization in this tick. The asset
    # keys in the values match the asset key in the corresponding key.
    will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]]
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]]
    candidates: AbstractSet[AssetKeyPartitionKey]
    daemon_context: "AssetDaemonContext"

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def previous_tick_evaluation(self) -> Optional["AutoMaterializeAssetEvaluation"]:
        """Returns the evaluation of the asset on the previous tick."""
        return self.cursor.latest_evaluation_by_asset_key.get(self.asset_key)

    @property
    def evaluation_time(self) -> datetime.datetime:
        """Returns the time at which this rule is being evaluated."""
        return self.instance_queryer.evaluation_time

    @property
    def auto_materialize_run_tags(self) -> Mapping[str, str]:
        return {
            AUTO_MATERIALIZE_TAG: "true",
            **self.instance_queryer.instance.auto_materialize_run_tags,
        }

    @functools.cached_property
    def previous_tick_requested_or_discarded_asset_partitions(
        self,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions that were requested or discarded on the previous tick."""
        if not self.previous_tick_evaluation:
            return set()
        return self.previous_tick_evaluation.get_requested_or_discarded_asset_partitions(
            asset_graph=self.asset_graph
        )

    @functools.cached_property
    def previous_tick_evaluated_asset_partitions(
        self,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions that were evaluated on the previous tick."""
        if not self.previous_tick_evaluation:
            return set()
        return self.previous_tick_evaluation.get_evaluated_asset_partitions(
            asset_graph=self.asset_graph
        )

    def get_previous_tick_results(self, rule: "AutoMaterializeRule") -> "RuleEvaluationResults":
        """Returns the results that were calculated for a given rule on the previous tick."""
        if not self.previous_tick_evaluation:
            return []
        return self.previous_tick_evaluation.get_rule_evaluation_results(
            rule_snapshot=rule.to_snapshot(), asset_graph=self.asset_graph
        )

    def get_candidates_not_evaluated_by_rule_on_previous_tick(
        self,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of candidates that were not evaluated by the rule that is currently being
        evaluated on the previous tick.

        Any asset partition that was evaluated by any rule on the previous tick must have been
        evaluated by *all* skip rules.
        """
        return self.candidates - self.previous_tick_evaluated_asset_partitions

    def get_candidates_with_updated_or_will_update_parents(
        self,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of candidate asset partitions whose parents have been updated since the
        last tick or will be requested on this tick.

        Many rules depend on the state of the asset's parents, so this function is useful for
        finding asset partitions that should be re-evaluated.
        """
        updated_parents = self.get_asset_partitions_with_updated_parents_since_previous_tick()
        will_update_parents = set(self.get_will_update_parent_mapping().keys())
        return self.candidates & (updated_parents | will_update_parents)

    def materialized_requested_or_discarded_since_previous_tick(
        self, asset_partition: AssetKeyPartitionKey
    ) -> bool:
        """Returns whether an asset partition has been materialized, requested, or discarded since
        the last tick.
        """
        if asset_partition in self.previous_tick_requested_or_discarded_asset_partitions:
            return True
        return self.instance_queryer.asset_partition_has_materialization_or_observation(
            asset_partition, after_cursor=self.cursor.latest_storage_id
        )

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
            if parent not in self.will_materialize_mapping.get(parent.asset_key, set())
            or not self.materializable_in_same_run(asset_partition.asset_key, parent.asset_key)
        }

    def get_asset_partitions_with_updated_parents_since_previous_tick(
        self
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions for the current key which have parents that updated
        since the last tick.
        """
        return self.daemon_context.get_asset_partitions_with_newly_updated_parents_for_key(
            self.asset_key
        )

    def get_will_update_parent_mapping(
        self,
    ) -> Mapping[AssetKeyPartitionKey, AbstractSet[AssetKey]]:
        """Returns a mapping from asset partitions of the current asset to the set of parent keys
        which will be requested this tick and can execute in the same run as the current asset.
        """
        will_update_parents_by_asset_partition = defaultdict(set)
        # these are the set of parents that will be requested this tick and can be materialized in
        # the same run as this asset
        for parent_key in self.asset_graph.get_parents(self.asset_key):
            if not self.materializable_in_same_run(self.asset_key, parent_key):
                continue
            for parent_partition in self.will_materialize_mapping.get(parent_key, set()):
                asset_partition = AssetKeyPartitionKey(
                    self.asset_key, parent_partition.partition_key
                )
                will_update_parents_by_asset_partition[asset_partition].add(parent_key)

        return will_update_parents_by_asset_partition

    def will_update_asset_partition(self, asset_partition: AssetKeyPartitionKey) -> bool:
        return asset_partition in self.will_materialize_mapping.get(
            asset_partition.asset_key, set()
        )

    def get_asset_partitions_by_asset_key(
        self,
        asset_partitions: AbstractSet[AssetKeyPartitionKey],
    ) -> Mapping[AssetKey, Set[AssetKeyPartitionKey]]:
        asset_partitions_by_asset_key: Dict[AssetKey, Set[AssetKeyPartitionKey]] = defaultdict(set)
        for parent in asset_partitions:
            asset_partitions_by_asset_key[parent.asset_key].add(parent)

        return asset_partitions_by_asset_key


class AutoMaterializeRule(ABC):
    """An AutoMaterializeRule defines a bit of logic which helps determine if a materialization
    should be kicked off for a given asset partition.

    Each rule can have one of two decision types, `MATERIALIZE` (indicating that an asset partition
    should be materialized) or `SKIP` (indicating that the asset partition should not be
    materialized).

    Materialize rules are evaluated first, and skip rules operate over the set of candidates that
    are produced by the materialize rules. Other than that, there is no ordering between rules.
    """

    @abstractproperty
    def decision_type(self) -> AutoMaterializeDecisionType:
        """The decision type of the rule (either `MATERIALIZE` or `SKIP`)."""
        ...

    @abstractproperty
    def description(self) -> str:
        """A human-readable description of this rule. As a basic guideline, this string should
        complete the sentence: 'Indicates an asset should be (materialize/skipped) when ____'.
        """
        ...

    def add_evaluation_data_from_previous_tick(
        self,
        context: RuleEvaluationContext,
        asset_partitions_by_evaluation_data: Mapping[
            Optional[AutoMaterializeRuleEvaluationData], Set[AssetKeyPartitionKey]
        ],
        should_use_past_data_fn: Callable[[AssetKeyPartitionKey], bool],
    ) -> "RuleEvaluationResults":
        """Combines a given set of evaluation data with evaluation data from the previous tick. The
        returned value will include the union of the evaluation data contained within
        `asset_partitions_by_evaluation_data` and the evaluation data calculated for asset
        partitions on the previous tick for which `should_use_past_data_fn` evaluates to `True`.

        Args:
            context: The current RuleEvaluationContext.
            asset_partitions_by_evaluation_data: A mapping from evaluation data to the set of asset
                partitions that the rule applies to.
            should_use_past_data_fn: A function that returns whether a given asset partition from the
                previous tick should be included in the results of this tick.
        """
        asset_partitions_by_evaluation_data = defaultdict(set, asset_partitions_by_evaluation_data)
        evaluated_asset_partitions = set().union(*asset_partitions_by_evaluation_data.values())
        for evaluation_data, asset_partitions in context.get_previous_tick_results(self):
            for ap in asset_partitions:
                # evaluated data from this tick takes precedence over data from the previous tick
                if ap in evaluated_asset_partitions:
                    continue
                elif should_use_past_data_fn(ap):
                    asset_partitions_by_evaluation_data[evaluation_data].add(ap)

        return list(asset_partitions_by_evaluation_data.items())

    @abstractmethod
    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        """The core evaluation function for the rule. This function takes in a context object and
        returns a mapping from evaluated rules to the set of asset partitions that the rule applies
        to.
        """
        ...

    @public
    @staticmethod
    def materialize_on_required_for_freshness() -> "MaterializeOnRequiredForFreshnessRule":
        """Materialize an asset partition if it is required to satisfy a freshness policy of this
        asset or one of its downstream assets.

        Note: This rule has no effect on partitioned assets.
        """
        return MaterializeOnRequiredForFreshnessRule()

    @public
    @staticmethod
    def materialize_on_cron(
        cron_schedule: str, timezone: str = "UTC", all_partitions: bool = False
    ) -> "MaterializeOnCronRule":
        """Materialize an asset partition if it has not been materialized since the latest cron
        schedule tick. For assets with a time component to their partitions_def, this rule will
        request all partitions that have been missed since the previous tick.

        Args:
            cron_schedule (str): A cron schedule string (e.g. "`0 * * * *`") indicating the ticks for
                which this rule should fire.
            timezone (str): The timezone in which this cron schedule should be evaluated. Defaults
                to "UTC".
            all_partitions (bool): If True, this rule fires for all partitions of this asset on each
                cron tick. If False, this rule fires only for the last partition of this asset.
                Defaults to False.
        """
        check.param_invariant(
            is_valid_cron_string(cron_schedule), "cron_schedule", "must be a valid cron string"
        )
        check.param_invariant(
            timezone in pytz.all_timezones_set, "timezone", "must be a valid timezone"
        )
        return MaterializeOnCronRule(
            cron_schedule=cron_schedule, timezone=timezone, all_partitions=all_partitions
        )

    @public
    @staticmethod
    def materialize_on_parent_updated(
        updated_parent_filter: Optional["AutoMaterializeAssetPartitionsFilter"] = None
    ) -> "MaterializeOnParentUpdatedRule":
        """Materialize an asset partition if one of its parents has been updated more recently
        than it has.

        Note: For time-partitioned or dynamic-partitioned assets downstream of an unpartitioned
        asset, this rule will only fire for the most recent partition of the downstream.

        Args:
            updated_parent_filter (Optional[AutoMaterializeAssetPartitionsFilter]): Filter to apply
                to updated parents. If a parent was updated but does not pass the filter criteria,
                then it won't count as updated for the sake of this rule.
        """
        return MaterializeOnParentUpdatedRule(updated_parent_filter=updated_parent_filter)

    @public
    @staticmethod
    def materialize_on_missing() -> "MaterializeOnMissingRule":
        """Materialize an asset partition if it has never been materialized before. This rule will
        not fire for non-root assets unless that asset's parents have been updated.
        """
        return MaterializeOnMissingRule()

    @public
    @staticmethod
    def skip_on_parent_missing() -> "SkipOnParentMissingRule":
        """Skip materializing an asset partition if one of its parent asset partitions has never
        been materialized (for regular assets) or observed (for observable source assets).
        """
        return SkipOnParentMissingRule()

    @public
    @staticmethod
    def skip_on_parent_outdated() -> "SkipOnParentOutdatedRule":
        """Skip materializing an asset partition if any of its parents has not incorporated the
        latest data from its ancestors.
        """
        return SkipOnParentOutdatedRule()

    @public
    @staticmethod
    def skip_on_not_all_parents_updated(
        require_update_for_all_parent_partitions: bool = False,
    ) -> "SkipOnNotAllParentsUpdatedRule":
        """Skip materializing an asset partition if any of its parents have not been updated since
        the asset's last materialization.

        Args:
            require_update_for_all_parent_partitions (Optional[bool]): Applies only to an unpartitioned
                asset or an asset partition that depends on more than one partition in any upstream asset.
                If true, requires all upstream partitions in each upstream asset to be materialized since
                the downstream asset's last materialization in order to update it. If false, requires at
                least one upstream partition in each upstream asset to be materialized since the downstream
                asset's last materialization in order to update it. Defaults to false.
        """
        return SkipOnNotAllParentsUpdatedRule(require_update_for_all_parent_partitions)

    @public
    @staticmethod
    def skip_on_required_but_nonexistent_parents() -> "SkipOnRequiredButNonexistentParentsRule":
        """Skip an asset partition if it depends on parent partitions that do not exist.

        For example, imagine a downstream asset is time-partitioned, starting in 2022, but has a
        time-partitioned parent which starts in 2023. This rule will skip attempting to materialize
        downstream partitions from before 2023, since the parent partitions do not exist.
        """
        return SkipOnRequiredButNonexistentParentsRule()

    @public
    @staticmethod
    def skip_on_backfill_in_progress(
        all_partitions: bool = False,
    ) -> "SkipOnBackfillInProgressRule":
        """Skip an asset's partitions if targeted by an in-progress backfill.

        Args:
            all_partitions (bool): If True, skips all partitions of the asset being backfilled,
                regardless of whether the specific partition is targeted by a backfill.
                If False, skips only partitions targeted by a backfill. Defaults to False.
        """
        return SkipOnBackfillInProgressRule(all_partitions)

    def to_snapshot(self) -> AutoMaterializeRuleSnapshot:
        """Returns a serializable snapshot of this rule for historical evaluations."""
        return AutoMaterializeRuleSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            decision_type=self.decision_type,
        )

    def __eq__(self, other) -> bool:
        # override the default NamedTuple __eq__ method to factor in types
        return type(self) == type(other) and super().__eq__(other)

    def __hash__(self) -> int:
        # override the default NamedTuple __hash__ method to factor in types
        return hash(hash(type(self)) + super().__hash__())


@whitelist_for_serdes
class MaterializeOnRequiredForFreshnessRule(
    AutoMaterializeRule, NamedTuple("_MaterializeOnRequiredForFreshnessRule", [])
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return "required to meet this or downstream asset's freshness policy"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        freshness_conditions = freshness_evaluation_results_for_asset_key(
            asset_key=context.asset_key,
            data_time_resolver=context.data_time_resolver,
            asset_graph=context.asset_graph,
            current_time=context.instance_queryer.evaluation_time,
            will_materialize_mapping=context.will_materialize_mapping,
            expected_data_time_mapping=context.expected_data_time_mapping,
        )
        return freshness_conditions


@whitelist_for_serdes
class MaterializeOnCronRule(
    AutoMaterializeRule,
    NamedTuple(
        "_MaterializeOnCronRule",
        [("cron_schedule", str), ("timezone", str), ("all_partitions", bool)],
    ),
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return f"not materialized since last cron schedule tick of '{self.cron_schedule}' (timezone: {self.timezone})"

    def missed_cron_ticks(self, context: RuleEvaluationContext) -> Sequence[datetime.datetime]:
        """Returns the cron ticks which have been missed since the previous cursor was generated."""
        if not context.cursor.latest_evaluation_timestamp:
            previous_dt = next(
                reverse_cron_string_iterator(
                    end_timestamp=context.evaluation_time.timestamp(),
                    cron_string=self.cron_schedule,
                    execution_timezone=self.timezone,
                )
            )
            return [previous_dt]
        missed_ticks = []
        for dt in cron_string_iterator(
            start_timestamp=context.cursor.latest_evaluation_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        ):
            if dt > context.evaluation_time:
                break
            missed_ticks.append(dt)
        return missed_ticks

    def get_asset_partitions_to_request(
        self, context: RuleEvaluationContext
    ) -> AbstractSet[AssetKeyPartitionKey]:
        missed_ticks = self.missed_cron_ticks(context)

        if not missed_ticks:
            return set()

        partitions_def = context.asset_graph.get_partitions_def(context.asset_key)
        if partitions_def is None:
            return {AssetKeyPartitionKey(context.asset_key)}

        # if all_partitions is set, then just return all partitions if any ticks have been missed
        if self.all_partitions:
            return {
                AssetKeyPartitionKey(context.asset_key, partition_key)
                for partition_key in partitions_def.get_partition_keys(
                    current_time=context.evaluation_time
                )
            }

        # for partitions_defs without a time component, just return the last partition if any ticks
        # have been missed
        time_partitions_def = get_time_partitions_def(partitions_def)
        if time_partitions_def is None:
            return {
                AssetKeyPartitionKey(context.asset_key, partitions_def.get_last_partition_key())
            }

        missed_time_partition_keys = filter(
            None,
            [
                time_partitions_def.get_last_partition_key(current_time=missed_tick)
                for missed_tick in missed_ticks
            ],
        )
        # for multi partitions definitions, request to materialize all partitions for each missed
        # cron schedule tick
        if isinstance(partitions_def, MultiPartitionsDefinition):
            return {
                AssetKeyPartitionKey(context.asset_key, partition_key)
                for time_partition_key in missed_time_partition_keys
                for partition_key in partitions_def.get_multipartition_keys_with_dimension_value(
                    partitions_def.time_window_dimension.name,
                    time_partition_key,
                    dynamic_partitions_store=context.instance_queryer,
                )
            }
        else:
            return {
                AssetKeyPartitionKey(context.asset_key, time_partition_key)
                for time_partition_key in missed_time_partition_keys
            }

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_to_request = self.get_asset_partitions_to_request(context)
        asset_partitions_by_evaluation_data = defaultdict(set)
        if asset_partitions_to_request:
            asset_partitions_by_evaluation_data[None].update(asset_partitions_to_request)
        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: not context.materialized_requested_or_discarded_since_previous_tick(
                ap
            ),
        )


@whitelist_for_serdes
@experimental
class AutoMaterializeAssetPartitionsFilter(
    NamedTuple(
        "_AutoMaterializeAssetPartitionsFilter",
        [("latest_run_required_tags", Optional[Mapping[str, str]])],
    )
):
    """A filter that can be applied to an asset partition, during auto-materialize evaluation, and
    returns a boolean for whether it passes.

    Attributes:
        latest_run_required_tags (Optional[Sequence[str]]): `passes` returns
            True if the run responsible for the latest materialization of the asset partition does
            not have all of these tags.
    """

    @property
    def description(self) -> str:
        return f"latest run includes required tags: {self.latest_run_required_tags}"

    def passes(
        self, context: RuleEvaluationContext, asset_partitions: Iterable[AssetKeyPartitionKey]
    ) -> Iterable[AssetKeyPartitionKey]:
        if self.latest_run_required_tags is None:
            return asset_partitions

        will_update_asset_partitions: Set[AssetKeyPartitionKey] = set()

        asset_partitions_by_latest_run_id: Dict[str, Set[AssetKeyPartitionKey]] = defaultdict(set)
        for asset_partition in asset_partitions:
            if context.will_update_asset_partition(asset_partition):
                will_update_asset_partitions.add(asset_partition)
            else:
                record = context.instance_queryer.get_latest_materialization_or_observation_record(
                    asset_partition
                )

                if record is None:
                    raise RuntimeError(
                        f"No materialization record found for asset partition {asset_partition}"
                    )

                asset_partitions_by_latest_run_id[record.run_id].add(asset_partition)

        if len(asset_partitions_by_latest_run_id) > 0:
            run_ids_with_required_tags = context.instance_queryer.instance.get_run_ids(
                filters=RunsFilter(
                    run_ids=list(asset_partitions_by_latest_run_id.keys()),
                    tags=self.latest_run_required_tags,
                )
            )
        else:
            run_ids_with_required_tags = set()

        updated_partitions_with_required_tags = {
            asset_partition
            for run_id, run_id_asset_partitions in asset_partitions_by_latest_run_id.items()
            if run_id in run_ids_with_required_tags
            for asset_partition in run_id_asset_partitions
        }

        if self.latest_run_required_tags.items() <= context.auto_materialize_run_tags.items():
            return will_update_asset_partitions | updated_partitions_with_required_tags
        else:
            return updated_partitions_with_required_tags

    def __hash__(self):
        return hash(frozenset((self.latest_run_required_tags or {}).items()))


@whitelist_for_serdes
class MaterializeOnParentUpdatedRule(
    AutoMaterializeRule,
    NamedTuple(
        "_MaterializeOnParentUpdatedRule",
        [("updated_parent_filter", Optional[AutoMaterializeAssetPartitionsFilter])],
    ),
):
    def __new__(cls, updated_parent_filter: Optional[AutoMaterializeAssetPartitionsFilter] = None):
        return super().__new__(cls, updated_parent_filter=updated_parent_filter)

    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        base = "upstream data has changed since latest materialization"
        if self.updated_parent_filter is not None:
            return f"{base} and matches filter '{self.updated_parent_filter.description}'"
        else:
            return base

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        """Evaluates the set of asset partitions of this asset whose parents have been updated,
        or will update on this tick.
        """
        will_update_parents_by_asset_partition = context.get_will_update_parent_mapping()

        # the set of asset partitions whose parents have been updated since last tick, or will be
        # requested this tick.
        has_or_will_update = (
            context.get_asset_partitions_with_updated_parents_since_previous_tick()
            | set(will_update_parents_by_asset_partition.keys())
        )

        asset_partitions_by_updated_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)
        asset_partitions_by_will_update_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)

        for asset_partition in has_or_will_update:
            parent_asset_partitions = context.asset_graph.get_parents_partitions(
                dynamic_partitions_store=context.instance_queryer,
                current_time=context.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions

            updated_parent_asset_partitions = context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                asset_partition,
                parent_asset_partitions,
                # do a precise check for updated parents, factoring in data versions, as long as
                # we're within reasonable limits on the number of partitions to check
                respect_materialization_data_versions=context.daemon_context.respect_materialization_data_versions
                and len(parent_asset_partitions | has_or_will_update) < 100,
                # ignore self-dependencies when checking for updated parents, to avoid historical
                # rematerializations from causing a chain of materializations to be kicked off
                ignored_parent_keys={context.asset_key},
            )
            for parent in updated_parent_asset_partitions:
                asset_partitions_by_updated_parents[parent].add(asset_partition)

            for parent in parent_asset_partitions:
                if context.will_update_asset_partition(parent):
                    asset_partitions_by_will_update_parents[parent].add(asset_partition)

        updated_and_will_update_parents = (
            asset_partitions_by_updated_parents.keys()
            | asset_partitions_by_will_update_parents.keys()
        )
        filtered_updated_and_will_update_parents = (
            self.updated_parent_filter.passes(context, updated_and_will_update_parents)
            if self.updated_parent_filter
            else updated_and_will_update_parents
        )

        updated_parent_assets_by_asset_partition: Dict[
            AssetKeyPartitionKey, Set[AssetKey]
        ] = defaultdict(set)
        will_update_parent_assets_by_asset_partition: Dict[
            AssetKeyPartitionKey, Set[AssetKey]
        ] = defaultdict(set)

        for updated_or_will_update_parent in filtered_updated_and_will_update_parents:
            for child in asset_partitions_by_updated_parents.get(updated_or_will_update_parent, []):
                updated_parent_assets_by_asset_partition[child].add(
                    updated_or_will_update_parent.asset_key
                )

            for child in asset_partitions_by_will_update_parents.get(
                updated_or_will_update_parent, []
            ):
                will_update_parent_assets_by_asset_partition[child].add(
                    updated_or_will_update_parent.asset_key
                )

        asset_partitions_by_evaluation_data = defaultdict(set)
        for asset_partition in (
            updated_parent_assets_by_asset_partition.keys()
            | will_update_parent_assets_by_asset_partition.keys()
        ):
            asset_partitions_by_evaluation_data[
                ParentUpdatedRuleEvaluationData(
                    updated_asset_keys=frozenset(
                        updated_parent_assets_by_asset_partition.get(asset_partition, [])
                    ),
                    will_update_asset_keys=frozenset(
                        will_update_parent_assets_by_asset_partition.get(asset_partition, [])
                    ),
                )
            ].add(asset_partition)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: not context.materialized_requested_or_discarded_since_previous_tick(
                ap
            ),
        )


@whitelist_for_serdes
class MaterializeOnMissingRule(AutoMaterializeRule, NamedTuple("_MaterializeOnMissingRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return "materialization is missing"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        """Evaluates the set of asset partitions for this asset which are missing and were not
        previously discarded. Currently only applies to root asset partitions and asset partitions
        with updated parents.
        """
        asset_partitions_by_evaluation_data = defaultdict(set)

        missing_asset_partitions = set(
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

        if missing_asset_partitions:
            asset_partitions_by_evaluation_data[None] = missing_asset_partitions

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in missing_asset_partitions
            and not context.materialized_requested_or_discarded_since_previous_tick(ap),
        )


@whitelist_for_serdes
class SkipOnParentOutdatedRule(AutoMaterializeRule, NamedTuple("_SkipOnParentOutdatedRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "waiting on upstream data to be up to date"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        candidates_to_evaluate = (
            context.get_candidates_not_evaluated_by_rule_on_previous_tick()
            | context.get_candidates_with_updated_or_will_update_parents()
        )
        for candidate in candidates_to_evaluate:
            outdated_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for parent in context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                if context.instance_queryer.have_ignorable_partition_mapping_for_outdated(
                    candidate.asset_key, parent.asset_key
                ):
                    continue
                outdated_ancestors.update(
                    context.instance_queryer.get_outdated_ancestors(asset_partition=parent)
                )
            if outdated_ancestors:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(outdated_ancestors))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in candidates_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnParentMissingRule(AutoMaterializeRule, NamedTuple("_SkipOnParentMissingRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "waiting on upstream data to be present"

    def evaluate_for_asset(
        self,
        context: RuleEvaluationContext,
    ) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        candidates_to_evaluate = (
            context.get_candidates_not_evaluated_by_rule_on_previous_tick()
            | context.get_candidates_with_updated_or_will_update_parents()
        )
        for candidate in candidates_to_evaluate:
            missing_parent_asset_keys = set()
            for parent in context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                # ignore non-observable sources, which will never have a materialization or observation
                if context.asset_graph.is_source(
                    parent.asset_key
                ) and not context.asset_graph.is_observable(parent.asset_key):
                    continue
                if not context.instance_queryer.asset_partition_has_materialization_or_observation(
                    parent
                ):
                    missing_parent_asset_keys.add(parent.asset_key)
            if missing_parent_asset_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(missing_parent_asset_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in candidates_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnNotAllParentsUpdatedRule(
    AutoMaterializeRule,
    NamedTuple(
        "_SkipOnNotAllParentsUpdatedRule", [("require_update_for_all_parent_partitions", bool)]
    ),
):
    """An auto-materialize rule that enforces that an asset can only be materialized if all parents
    have been materialized since the asset's last materialization.

    Attributes:
        require_update_for_all_parent_partitions (Optional[bool]): Applies only to an unpartitioned
            asset or an asset partition that depends on more than one partition in any upstream asset.
            If true, requires all upstream partitions in each upstream asset to be materialized since
            the downstream asset's last materialization in order to update it. If false, requires at
            least one upstream partition in each upstream asset to be materialized since the downstream
            asset's last materialization in order to update it. Defaults to false.
    """

    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        if self.require_update_for_all_parent_partitions is False:
            return "waiting on upstream data to be updated"
        else:
            return "waiting until all upstream partitions are updated"

    def evaluate_for_asset(
        self,
        context: RuleEvaluationContext,
    ) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        candidates_to_evaluate = (
            context.get_candidates_not_evaluated_by_rule_on_previous_tick()
            | context.get_candidates_with_updated_or_will_update_parents()
        )
        for candidate in candidates_to_evaluate:
            parent_partitions = context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                context.asset_key,
                candidate.partition_key,
            ).parent_partitions

            updated_parent_partitions = (
                context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                    candidate,
                    parent_partitions,
                    context.daemon_context.respect_materialization_data_versions,
                    ignored_parent_keys=set(),
                )
                | set().union(
                    *[
                        context.will_materialize_mapping.get(parent, set())
                        for parent in context.asset_graph.get_parents(context.asset_key)
                    ]
                )
            )

            if self.require_update_for_all_parent_partitions:
                # All upstream partitions must be updated in order for the candidate to be updated
                non_updated_parent_keys = {
                    parent.asset_key for parent in parent_partitions - updated_parent_partitions
                }
            else:
                # At least one upstream partition in each upstream asset must be updated in order
                # for the candidate to be updated
                parent_asset_keys = context.asset_graph.get_parents(context.asset_key)
                updated_parent_partitions_by_asset_key = context.get_asset_partitions_by_asset_key(
                    updated_parent_partitions
                )
                non_updated_parent_keys = {
                    parent
                    for parent in parent_asset_keys
                    if not updated_parent_partitions_by_asset_key.get(parent)
                }

            # do not require past partitions of this asset to be updated
            non_updated_parent_keys -= {context.asset_key}

            if non_updated_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(non_updated_parent_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in candidates_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnRequiredButNonexistentParentsRule(
    AutoMaterializeRule, NamedTuple("_SkipOnRequiredButNonexistentParentsRule", [])
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "required parent partitions do not exist"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        candidates_to_evaluate = context.get_candidates_not_evaluated_by_rule_on_previous_tick()
        for candidate in candidates_to_evaluate:
            nonexistent_parent_partitions = context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                candidate.asset_key,
                candidate.partition_key,
            ).required_but_nonexistent_parents_partitions

            nonexistent_parent_keys = {parent.asset_key for parent in nonexistent_parent_partitions}
            if nonexistent_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(nonexistent_parent_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in candidates_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnBackfillInProgressRule(
    AutoMaterializeRule,
    NamedTuple("_SkipOnBackfillInProgressRule", [("all_partitions", bool)]),
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        if self.all_partitions:
            return "part of an asset targeted by an in-progress backfill"
        else:
            return "targeted by an in-progress backfill"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        backfill_in_progress_candidates: AbstractSet[AssetKeyPartitionKey] = set()
        backfilling_subset = (
            context.instance_queryer.get_active_backfill_target_asset_graph_subset()
        )

        if self.all_partitions:
            backfill_in_progress_candidates = {
                candidate
                for candidate in context.candidates
                if candidate.asset_key in backfilling_subset.asset_keys
            }
        else:
            backfill_in_progress_candidates = {
                candidate for candidate in context.candidates if candidate in backfilling_subset
            }

        if backfill_in_progress_candidates:
            return [(None, backfill_in_progress_candidates)]

        return []


@whitelist_for_serdes
class DiscardOnMaxMaterializationsExceededRule(
    AutoMaterializeRule, NamedTuple("_DiscardOnMaxMaterializationsExceededRule", [("limit", int)])
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.DISCARD

    @property
    def description(self) -> str:
        return f"exceeds {self.limit} materialization(s) per minute"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        # the set of asset partitions which exceed the limit
        rate_limited_asset_partitions = set(
            sorted(
                context.candidates,
                key=lambda x: sort_key_for_asset_partition(context.asset_graph, x),
            )[self.limit :]
        )
        if rate_limited_asset_partitions:
            return [(None, rate_limited_asset_partitions)]
        return []
