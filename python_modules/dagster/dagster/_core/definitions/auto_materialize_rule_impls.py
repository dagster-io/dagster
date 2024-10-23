import datetime
import os
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
)

from dagster._annotations import experimental
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeDecisionType,
    ParentUpdatedRuleEvaluationData,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.base_asset_graph import sort_key_for_asset_partition
from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
    ValidAssetSubset,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_based_auto_materialize import (
    freshness_evaluation_results_for_asset_key,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    get_time_partitions_def,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, RunsFilter
from dagster._core.storage.tags import AUTO_MATERIALIZE_TAG
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.schedules import cron_string_iterator, reverse_cron_string_iterator

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationResult,
    )
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )


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

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        true_subset, subsets_with_metadata = freshness_evaluation_results_for_asset_key(
            context.legacy_context.root_context
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


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

    def missed_cron_ticks(self, context: "AutomationContext") -> Sequence[datetime.datetime]:
        """Returns the cron ticks which have been missed since the previous cursor was generated."""
        # if it's the first time evaluating this rule, then just count the latest tick as missed
        if (
            not context.legacy_context.node_cursor
            or not context.legacy_context.previous_evaluation_timestamp
        ):
            previous_dt = next(
                reverse_cron_string_iterator(
                    end_timestamp=context.legacy_context.evaluation_time.timestamp(),
                    cron_string=self.cron_schedule,
                    execution_timezone=self.timezone,
                )
            )
            return [previous_dt]
        missed_ticks = []
        for dt in cron_string_iterator(
            start_timestamp=context.legacy_context.previous_evaluation_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        ):
            if dt > context.legacy_context.evaluation_time:
                break
            missed_ticks.append(dt)
        return missed_ticks

    def get_new_candidate_asset_partitions(
        self,
        context: "AutomationContext",
        missed_ticks: Sequence[datetime.datetime],
    ) -> AbstractSet[AssetKeyPartitionKey]:
        if not missed_ticks:
            return set()

        partitions_def = context.legacy_context.partitions_def
        if partitions_def is None:
            return {AssetKeyPartitionKey(context.legacy_context.asset_key)}

        # if all_partitions is set, then just return all partitions if any ticks have been missed
        if self.all_partitions:
            return {
                AssetKeyPartitionKey(context.legacy_context.asset_key, partition_key)
                for partition_key in partitions_def.get_partition_keys(
                    current_time=context.legacy_context.evaluation_time,
                    dynamic_partitions_store=context.legacy_context.instance_queryer,
                )
            }

        # for partitions_defs without a time component, just return the last partition if any ticks
        # have been missed
        time_partitions_def = get_time_partitions_def(partitions_def)
        if time_partitions_def is None:
            return {
                AssetKeyPartitionKey(
                    context.legacy_context.asset_key,
                    partitions_def.get_last_partition_key(
                        dynamic_partitions_store=context.legacy_context.instance_queryer
                    ),
                )
            }

        missed_time_partition_keys = filter(
            None,
            [
                time_partitions_def.get_last_partition_key(
                    current_time=missed_tick,
                    dynamic_partitions_store=context.legacy_context.instance_queryer,
                )
                for missed_tick in missed_ticks
            ],
        )
        # for multi partitions definitions, request to materialize all partitions for each missed
        # cron schedule tick
        if isinstance(partitions_def, MultiPartitionsDefinition):
            return {
                AssetKeyPartitionKey(context.legacy_context.asset_key, partition_key)
                for time_partition_key in missed_time_partition_keys
                for partition_key in partitions_def.get_multipartition_keys_with_dimension_value(
                    partitions_def.time_window_dimension.name,
                    time_partition_key,
                    dynamic_partitions_store=context.legacy_context.instance_queryer,
                )
            }
        else:
            return {
                AssetKeyPartitionKey(context.legacy_context.asset_key, time_partition_key)
                for time_partition_key in missed_time_partition_keys
            }

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        missed_ticks = self.missed_cron_ticks(context)
        new_asset_partitions = self.get_new_candidate_asset_partitions(context, missed_ticks)

        # if it's the first time evaluating this rule, must query for the actual subset that has
        # been materialized since the previous cron tick, as materializations may have happened
        # before the previous evaluation, which
        # `context.legacy_context.materialized_requested_or_discarded_since_previous_tick_subset` would not capture
        if context.legacy_context.node_cursor is None:
            new_asset_partitions -= ValidAssetSubset.coerce_from_subset(
                context.legacy_context.instance_queryer.get_asset_subset_updated_after_time(
                    asset_key=context.legacy_context.asset_key, after_time=missed_ticks[-1]
                ),
                context.partitions_def,
            ).asset_partitions

        asset_subset_to_request = ValidAssetSubset.from_asset_partitions_set(
            context.legacy_context.asset_key,
            context.legacy_context.partitions_def,
            new_asset_partitions,
        ) | (
            ValidAssetSubset.coerce_from_subset(
                context.legacy_context.previous_true_subset, context.legacy_context.partitions_def
            )
            - context.legacy_context.materialized_requested_or_discarded_since_previous_tick_subset
        )

        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            asset_subset_to_request
        )
        return AutomationResult(context, true_subset=true_subset)


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
            True if the run responsible for the latest materialization of the asset partition
            has all of these tags.
    """

    @property
    def description(self) -> str:
        return f"latest run includes required tags: {self.latest_run_required_tags}"

    def passes(
        self,
        context: "AutomationContext",
        asset_partitions: Iterable[AssetKeyPartitionKey],
    ) -> Iterable[AssetKeyPartitionKey]:
        if self.latest_run_required_tags is None:
            return asset_partitions

        will_update_asset_partitions: Set[AssetKeyPartitionKey] = set()
        storage_ids_to_fetch_by_key: Dict[AssetKey, List[int]] = defaultdict(list)

        for asset_partition in asset_partitions:
            if context.legacy_context.will_update_asset_partition(asset_partition):
                will_update_asset_partitions.add(asset_partition)
            else:
                latest_storage_id = context.legacy_context.instance_queryer.get_latest_materialization_or_observation_storage_id(
                    asset_partition=asset_partition
                )
                if latest_storage_id is not None:
                    storage_ids_to_fetch_by_key[asset_partition.asset_key].append(latest_storage_id)

        asset_partitions_by_latest_run_id: Dict[str, Set[AssetKeyPartitionKey]] = defaultdict(set)

        step = int(os.getenv("DAGSTER_ASSET_DAEMON_RUN_TAGS_EVENT_FETCH_LIMIT", "1000"))

        for asset_key, storage_ids_to_fetch in storage_ids_to_fetch_by_key.items():
            for i in range(0, len(storage_ids_to_fetch), step):
                storage_ids = storage_ids_to_fetch[i : i + step]
                fetch_records = (
                    context.legacy_context.instance_queryer.instance.fetch_observations
                    if context.legacy_context.asset_graph.get(asset_key).is_observable
                    else context.legacy_context.instance_queryer.instance.fetch_materializations
                )
                for record in fetch_records(
                    records_filter=AssetRecordsFilter(
                        asset_key=asset_key,
                        storage_ids=storage_ids,
                    ),
                    limit=step,
                ).records:
                    asset_partitions_by_latest_run_id[record.run_id].add(
                        AssetKeyPartitionKey(asset_key, record.partition_key)
                    )

        run_ids_with_required_tags = set()

        if len(asset_partitions_by_latest_run_id) > 0:
            run_step = int(os.getenv("DAGSTER_ASSET_DAEMON_RUN_TAGS_RUN_FETCH_LIMIT", "1000"))

            required_tag_items = self.latest_run_required_tags.items()

            run_ids_to_fetch = list(asset_partitions_by_latest_run_id.keys())
            for i in range(0, len(run_ids_to_fetch), run_step):
                run_ids = run_ids_to_fetch[i : i + run_step]
                runs = context.legacy_context.instance_queryer.instance.get_runs(
                    filters=RunsFilter(run_ids=run_ids)
                )
                run_ids_with_required_tags.update(
                    {run.run_id for run in runs if required_tag_items <= run.tags.items()}
                )

        updated_partitions_with_required_tags = {
            asset_partition
            for run_id, run_id_asset_partitions in asset_partitions_by_latest_run_id.items()
            if run_id in run_ids_with_required_tags
            for asset_partition in run_id_asset_partitions
        }

        if (
            self.latest_run_required_tags.items()
            <= {
                AUTO_MATERIALIZE_TAG: "true",
                **context.legacy_context.auto_materialize_run_tags,
            }.items()
        ):
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

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        """Evaluates the set of asset partitions of this asset whose parents have been updated,
        or will update on this tick.
        """
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        asset_partitions_by_updated_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)
        asset_partitions_by_will_update_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)

        subset_to_evaluate = context.legacy_context.parent_has_or_will_update_subset
        for asset_partition in subset_to_evaluate.asset_partitions:
            parent_asset_partitions = context.legacy_context.asset_graph.get_parents_partitions(
                dynamic_partitions_store=context.legacy_context.instance_queryer,
                current_time=context.legacy_context.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions

            updated_parent_asset_partitions = context.legacy_context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                asset_partition=asset_partition,
                parent_asset_partitions=parent_asset_partitions,
                # do a precise check for updated parents, factoring in data versions, as long as
                # we're within reasonable limits on the number of partitions to check
                respect_materialization_data_versions=context.legacy_context.respect_materialization_data_versions
                and len(parent_asset_partitions) + subset_to_evaluate.size < 100,
                # ignore self-dependencies when checking for updated parents, to avoid historical
                # rematerializations from causing a chain of materializations to be kicked off
                ignored_parent_keys={context.legacy_context.asset_key},
            )
            for parent in updated_parent_asset_partitions:
                asset_partitions_by_updated_parents[parent].add(asset_partition)

            for parent in parent_asset_partitions:
                if context.legacy_context.will_update_asset_partition(parent):
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

        updated_parent_assets_by_asset_partition: Dict[AssetKeyPartitionKey, Set[AssetKey]] = (
            defaultdict(set)
        )
        will_update_parent_assets_by_asset_partition: Dict[AssetKeyPartitionKey, Set[AssetKey]] = (
            defaultdict(set)
        )

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
                ).frozen_metadata
            ].add(asset_partition)

        true_subset, subsets_with_metadata = (
            context.legacy_context.add_evaluation_data_from_previous_tick(
                asset_partitions_by_evaluation_data,
                ignore_subset=context.legacy_context.materialized_requested_or_discarded_since_previous_tick_subset,
            )
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


@whitelist_for_serdes
class MaterializeOnMissingRule(AutoMaterializeRule, NamedTuple("_MaterializeOnMissingRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return "materialization is missing"

    def get_handled_subset(self, context: "AutomationContext") -> SerializableEntitySubset:
        """Returns the AssetSubset which has been handled (materialized, requested, or discarded).
        Accounts for cases in which the partitions definition may have changed between ticks.
        """
        previous_handled_subset = (
            context.legacy_context.node_cursor.get_structured_cursor(SerializableEntitySubset)
            if context.legacy_context.node_cursor
            else None
        )
        if (
            previous_handled_subset is None
            or not previous_handled_subset.is_compatible_with_partitions_def(context.partitions_def)
        ):
            previous_handled_subset = (
                context.legacy_context.instance_queryer.get_materialized_asset_subset(
                    asset_key=context.legacy_context.asset_key
                )
            )

        return (
            context.legacy_context.materialized_since_previous_tick_subset
            | context.legacy_context.previous_tick_requested_subset
            | previous_handled_subset
        )

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        """Evaluates the set of asset partitions for this asset which are missing and were not
        previously discarded.
        """
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        if (
            context.legacy_context.asset_key
            in context.legacy_context.asset_graph.root_executable_asset_keys
        ):
            handled_subset = self.get_handled_subset(context)
            unhandled_candidates = (
                context.legacy_context.candidate_subset
                & ValidAssetSubset.coerce_from_subset(
                    handled_subset, context.legacy_context.partitions_def
                ).inverse(
                    context.legacy_context.partitions_def,
                    context.legacy_context.evaluation_time,
                    context.legacy_context.instance_queryer,
                )
                if handled_subset.size > 0
                else context.legacy_context.candidate_subset
            )
        else:
            # to avoid causing potential perf issues, we are maintaing the previous behavior of
            # only marking a non-root asset as missing if at least one of its parents has updated
            # since the previous tick.
            # on top of this, we also check the latest time partition of the asset to see if it's
            # missing on the tick that it pops into existence
            asset_partitions_to_evaluate = (
                context.legacy_context.candidate_parent_has_or_will_update_subset.asset_partitions
            )
            if isinstance(context.legacy_context.partitions_def, TimeWindowPartitionsDefinition):
                last_partition_key = context.legacy_context.partitions_def.get_last_partition_key(
                    current_time=context.legacy_context.evaluation_time
                )
                previous_last_partition_key = (
                    context.legacy_context.partitions_def.get_last_partition_key(
                        current_time=datetime.datetime.fromtimestamp(
                            context.legacy_context.previous_evaluation_timestamp or 0,
                            tz=datetime.timezone.utc,
                        )
                    )
                )
                if last_partition_key != previous_last_partition_key:
                    asset_partitions_to_evaluate |= {
                        AssetKeyPartitionKey(context.legacy_context.asset_key, last_partition_key)
                    }

            handled_subset = None
            unhandled_candidates = (
                ValidAssetSubset.from_asset_partitions_set(
                    context.legacy_context.asset_key,
                    context.legacy_context.partitions_def,
                    {
                        ap
                        for ap in asset_partitions_to_evaluate
                        if not context.legacy_context.instance_queryer.asset_partition_has_materialization_or_observation(
                            ap
                        )
                    },
                )
                | context.legacy_context.previous_true_subset
            ) - context.legacy_context.previous_tick_requested_subset

        return AutomationResult(
            context,
            true_subset=context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
                unhandled_candidates
            ),
            # we keep track of the handled subset instead of the unhandled subset because new
            # partitions may spontaneously jump into existence at any time
            structured_cursor=handled_subset,
        )


@whitelist_for_serdes
class SkipOnParentOutdatedRule(AutoMaterializeRule, NamedTuple("_SkipOnParentOutdatedRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "waiting on upstream data to be up to date"

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.legacy_context.candidates_not_evaluated_on_previous_tick_subset
            | context.legacy_context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            outdated_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for (
                parent
            ) in context.legacy_context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                if context.legacy_context.instance_queryer.have_ignorable_partition_mapping_for_outdated(
                    candidate.asset_key, parent.asset_key
                ):
                    continue
                outdated_ancestors.update(
                    context.legacy_context.instance_queryer.get_outdated_ancestors(
                        asset_partition=parent
                    )
                )
            if outdated_ancestors:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(outdated_ancestors)).frozen_metadata
                ].add(candidate)

        true_subset, subsets_with_metadata = (
            context.legacy_context.add_evaluation_data_from_previous_tick(
                asset_partitions_by_evaluation_data, ignore_subset=subset_to_evaluate
            )
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


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
        context: "AutomationContext",
    ) -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.legacy_context.candidates_not_evaluated_on_previous_tick_subset
            | context.legacy_context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            missing_parent_asset_keys = set()
            for (
                parent
            ) in context.legacy_context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                # ignore missing or unexecutable assets, which will never have a materialization or
                # observation
                if not (
                    context.legacy_context.asset_graph.has(parent.asset_key)
                    and context.legacy_context.asset_graph.get(parent.asset_key).is_executable
                ):
                    continue
                if not context.legacy_context.instance_queryer.asset_partition_has_materialization_or_observation(
                    parent
                ):
                    missing_parent_asset_keys.add(parent.asset_key)
            if missing_parent_asset_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(
                        frozenset(missing_parent_asset_keys)
                    ).frozen_metadata
                ].add(candidate)

        true_subset, subsets_with_metadata = (
            context.legacy_context.add_evaluation_data_from_previous_tick(
                asset_partitions_by_evaluation_data, ignore_subset=subset_to_evaluate
            )
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


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
        context: "AutomationContext",
    ) -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.legacy_context.candidates_not_evaluated_on_previous_tick_subset
            | context.legacy_context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            parent_partitions = context.legacy_context.asset_graph.get_parents_partitions(
                context.legacy_context.instance_queryer,
                context.legacy_context.instance_queryer.evaluation_time,
                context.legacy_context.asset_key,
                candidate.partition_key,
            ).parent_partitions

            updated_parent_partitions = (
                context.legacy_context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                    asset_partition=candidate,
                    parent_asset_partitions=parent_partitions,
                    respect_materialization_data_versions=context.legacy_context.respect_materialization_data_versions,
                    ignored_parent_keys=set(),
                )
                | context.legacy_context.parent_will_update_subset.asset_partitions
            )

            if self.require_update_for_all_parent_partitions:
                # All upstream partitions must be updated in order for the candidate to be updated
                non_updated_parent_keys = {
                    parent.asset_key for parent in parent_partitions - updated_parent_partitions
                }
            else:
                # At least one upstream partition in each upstream asset must be updated in order
                # for the candidate to be updated
                parent_asset_keys = context.legacy_context.asset_graph.get(
                    context.legacy_context.asset_key
                ).parent_keys
                updated_parent_keys = {ap.asset_key for ap in updated_parent_partitions}
                non_updated_parent_keys = parent_asset_keys - updated_parent_keys

            # do not require past partitions of this asset to be updated
            non_updated_parent_keys -= {context.legacy_context.asset_key}

            if non_updated_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(
                        frozenset(non_updated_parent_keys)
                    ).frozen_metadata
                ].add(candidate)

        true_subset, subsets_with_metadata = (
            context.legacy_context.add_evaluation_data_from_previous_tick(
                asset_partitions_by_evaluation_data, ignore_subset=subset_to_evaluate
            )
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


@whitelist_for_serdes
class SkipOnNotAllParentsUpdatedSinceCronRule(
    AutoMaterializeRule,
    NamedTuple(
        "_SkipOnNotAllParentsUpdatedSinceCronRule",
        [("cron_schedule", str), ("timezone", str)],
    ),
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return f"waiting until all upstream assets have updated since the last cron schedule tick of '{self.cron_schedule}' (timezone: {self.timezone})"

    def passed_time_window(self, context: "AutomationContext") -> TimeWindow:
        """Returns the window of time that has passed between the previous two cron ticks. All
        parent assets must contain all data from this time window in order for this asset to be
        materialized.
        """
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=context.legacy_context.evaluation_time.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        )
        end_time = next(previous_ticks)
        start_time = next(previous_ticks)

        return TimeWindow(start=start_time, end=end_time)

    def get_parent_subset_updated_since_cron(
        self,
        context: "AutomationContext",
        parent_asset_key: AssetKey,
        passed_time_window: TimeWindow,
    ) -> ValidAssetSubset:
        """Returns the AssetSubset of a given parent asset that has been updated since the end of
        the previous cron tick. If a value for this parent asset was computed on the previous
        evaluation, and that evaluation happened within the same cron tick as the current evaluation,
        then this value will be calculated incrementally from the previous value to avoid expensive
        queries.
        """
        parent_partitions_def = context.asset_graph.get(parent_asset_key).partitions_def
        if (
            # first tick of evaluating this condition
            context.legacy_context.node_cursor is None
            or context.legacy_context.previous_evaluation_timestamp is None
            # This additional check is neccessary as it is possible for this cursor to be None
            # even if the previous state is not None in the case that this asset and none of its
            # parents have been detected as materialized at any point. While in theory this should
            # not cause issues, in past versions we were not properly capturing materializations
            # of external assets, causing this detection to be faulty. This ensures that we can
            # properly re-calculate this value even in the case that we've incorrectly considered
            # a parent as unmaterialized in the past.
            or context.legacy_context.previous_max_storage_id is None
            # new cron tick has happened since the previous tick
            or passed_time_window.end.timestamp()
            > context.legacy_context.previous_evaluation_timestamp
        ):
            return ValidAssetSubset.coerce_from_subset(
                context.legacy_context.instance_queryer.get_asset_subset_updated_after_time(
                    asset_key=parent_asset_key, after_time=passed_time_window.end
                ),
                parent_partitions_def,
            )
        else:
            # previous state still valid
            previous_parent_subsets = (
                context.legacy_context.node_cursor.get_structured_cursor(list) or []
            )
            previous_parent_subset = next(
                (s for s in previous_parent_subsets if s.key == parent_asset_key),
                ValidAssetSubset.empty(
                    parent_asset_key, context.asset_graph.get(parent_asset_key).partitions_def
                ),
            )

            # the set of asset partitions that have been updated since the previous evaluation
            new_parent_subset = ValidAssetSubset.coerce_from_subset(
                context.legacy_context.instance_queryer.get_asset_subset_updated_after_cursor(
                    asset_key=parent_asset_key,
                    after_cursor=context.legacy_context.previous_max_storage_id,
                ),
                parent_partitions_def,
            )
            return new_parent_subset | previous_parent_subset

    def get_parent_subsets_updated_since_cron_by_key(
        self, context: "AutomationContext", passed_time_window: TimeWindow
    ) -> Mapping[AssetKey, ValidAssetSubset]:
        """Returns a mapping of parent asset keys to the AssetSubset of each parent that has been
        updated since the end of the previous cron tick. Does not compute this value for time-window
        partitioned parents, as their partitions encode the time windows they have processed.
        """
        updated_subsets_by_key = {}
        for parent_asset_key in context.legacy_context.asset_graph.get(
            context.legacy_context.asset_key
        ).parent_keys:
            # no need to incrementally calculate updated time-window partitions definitions, as
            # their partitions encode the time windows they have processed.
            if isinstance(
                context.legacy_context.asset_graph.get(parent_asset_key).partitions_def,
                TimeWindowPartitionsDefinition,
            ):
                continue
            updated_subsets_by_key[parent_asset_key] = self.get_parent_subset_updated_since_cron(
                context, parent_asset_key, passed_time_window
            )
        return updated_subsets_by_key

    def parent_updated_since_cron(
        self,
        context: "AutomationContext",
        passed_time_window: TimeWindow,
        parent_asset_key: AssetKey,
        child_asset_partition: AssetKeyPartitionKey,
        updated_parent_subset: ValidAssetSubset,
    ) -> bool:
        """Returns if, for a given child asset partition, the given parent asset been updated with
        information from the required time window.
        """
        parent_partitions_def = context.legacy_context.asset_graph.get(
            parent_asset_key
        ).partitions_def

        if isinstance(parent_partitions_def, TimeWindowPartitionsDefinition):
            # for time window partitions definitions, we simply assert that all time partitions that
            # were newly created between the previous cron ticks have been materialized
            required_parent_partitions = parent_partitions_def.get_partition_keys_in_time_window(
                time_window=passed_time_window
            )

            # for time window partitions definitions, we simply assert that all time partitions that
            return all(
                AssetKeyPartitionKey(parent_asset_key, partition_key)
                in context.legacy_context.instance_queryer.get_materialized_asset_subset(
                    asset_key=parent_asset_key
                )
                for partition_key in required_parent_partitions
            )
        # for all other partitions definitions, we assert that all parent partition keys have
        # been materialized since the previous cron tick
        else:
            if parent_partitions_def is None:
                non_updated_parent_asset_partitions = updated_parent_subset.inverse(
                    parent_partitions_def
                ).asset_partitions
            else:
                parent_subset = (
                    context.legacy_context.asset_graph.get_parent_partition_keys_for_child(
                        child_asset_partition.partition_key,
                        parent_asset_key,
                        child_asset_partition.asset_key,
                        context.legacy_context.instance_queryer,
                        context.legacy_context.evaluation_time,
                    ).partitions_subset
                )

                non_updated_parent_asset_partitions = (
                    ValidAssetSubset(key=parent_asset_key, value=parent_subset)
                    - updated_parent_subset
                ).asset_partitions

            return not any(
                not context.legacy_context.will_update_asset_partition(p)
                for p in non_updated_parent_asset_partitions
            )

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        passed_time_window = self.passed_time_window(context)
        has_new_passed_time_window = passed_time_window.end.timestamp() > (
            context.legacy_context.previous_evaluation_timestamp or 0
        )
        updated_subsets_by_key = self.get_parent_subsets_updated_since_cron_by_key(
            context, passed_time_window
        )

        # only need to evaluate net-new candidates and candidates whose parents have updated, unless
        # this is the first tick after a new cron schedule tick
        subset_to_evaluate = (
            (
                context.legacy_context.candidates_not_evaluated_on_previous_tick_subset
                | context.legacy_context.candidate_parent_has_or_will_update_subset
            )
            if not has_new_passed_time_window
            else context.legacy_context.candidate_subset
        )

        # the set of candidates for whom all parents have been updated since the previous cron tick
        all_parents_updated_subset = ValidAssetSubset.from_asset_partitions_set(
            context.legacy_context.asset_key,
            context.legacy_context.partitions_def,
            {
                candidate
                for candidate in subset_to_evaluate.asset_partitions
                if all(
                    self.parent_updated_since_cron(
                        context,
                        passed_time_window,
                        parent_asset_key,
                        candidate,
                        updated_subsets_by_key.get(
                            parent_asset_key,
                            ValidAssetSubset.empty(
                                parent_asset_key,
                                context.asset_graph.get(parent_asset_key).partitions_def,
                            ),
                        ),
                    )
                    for parent_asset_key in context.legacy_context.asset_graph.get(
                        candidate.asset_key
                    ).parent_keys
                )
            },
        )
        # if your parents were all updated since the previous cron tick on the previous evaluation,
        # that will still be true unless a new cron tick has happened since the previous evaluation
        if not has_new_passed_time_window:
            all_parents_updated_subset = (
                ValidAssetSubset.coerce_from_subset(
                    context.legacy_context.previous_candidate_subset,
                    context.legacy_context.partitions_def,
                )
                - context.legacy_context.previous_true_subset
            ) | all_parents_updated_subset

        return AutomationResult(
            context,
            true_subset=context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
                context.legacy_context.candidate_subset - all_parents_updated_subset
            ),
            structured_cursor=list(updated_subsets_by_key.values()),
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

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        asset_partitions_by_evaluation_data = defaultdict(set)

        subset_to_evaluate = (
            context.legacy_context.candidates_not_evaluated_on_previous_tick_subset
            | context.legacy_context.candidate_parent_has_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            nonexistent_parent_partitions = (
                context.legacy_context.asset_graph.get_parents_partitions(
                    context.legacy_context.instance_queryer,
                    context.legacy_context.instance_queryer.evaluation_time,
                    candidate.asset_key,
                    candidate.partition_key,
                ).required_but_nonexistent_parents_partitions
            )

            nonexistent_parent_keys = {parent.asset_key for parent in nonexistent_parent_partitions}
            if nonexistent_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(
                        frozenset(nonexistent_parent_keys)
                    ).frozen_metadata
                ].add(candidate)

        true_subset, subsets_with_metadata = (
            context.legacy_context.add_evaluation_data_from_previous_tick(
                asset_partitions_by_evaluation_data, ignore_subset=subset_to_evaluate
            )
        )
        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset, subsets_with_metadata=subsets_with_metadata)


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

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        backfilling_subset = ValidAssetSubset.coerce_from_subset(
            # this backfilling subset is aware of the current partitions definitions, and so will
            # be valid
            (
                context.legacy_context.instance_queryer.get_active_backfill_target_asset_graph_subset()
            ).get_asset_subset(
                context.legacy_context.asset_key, context.legacy_context.asset_graph
            ),
            context.legacy_context.partitions_def,
        )

        if backfilling_subset.size == 0:
            true_subset = context.legacy_context.empty_subset()
        elif self.all_partitions:
            true_subset = context.legacy_context.candidate_subset
        else:
            true_subset = context.legacy_context.candidate_subset & backfilling_subset

        true_subset = context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
            true_subset
        )
        return AutomationResult(context, true_subset)


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

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        # the set of asset partitions which exceed the limit
        rate_limited_asset_partitions = set(
            sorted(
                context.legacy_context.candidate_subset.asset_partitions,
                key=lambda x: sort_key_for_asset_partition(context.legacy_context.asset_graph, x),
            )[self.limit :]
        )

        return AutomationResult(
            context,
            context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
                ValidAssetSubset.from_asset_partitions_set(
                    context.legacy_context.asset_key,
                    context.legacy_context.partitions_def,
                    rate_limited_asset_partitions,
                )
            ),
        )


@whitelist_for_serdes
class SkipOnRunInProgressRule(AutoMaterializeRule, NamedTuple("_SkipOnRunInProgressRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "in-progress run for asset"

    def evaluate_for_asset(self, context: "AutomationContext") -> "AutomationResult":
        from dagster._core.definitions.declarative_automation.automation_condition import (
            AutomationResult,
        )

        if context.legacy_context.partitions_def is not None:
            raise DagsterInvariantViolationError(
                "SkipOnRunInProgressRule is currently only support for non-partitioned assets."
            )
        instance = context.legacy_context.instance_queryer.instance
        planned_materialization_info = (
            instance.event_log_storage.get_latest_planned_materialization_info(
                context.legacy_context.asset_key
            )
        )
        if planned_materialization_info:
            dagster_run = instance.get_run_by_id(planned_materialization_info.run_id)
            if dagster_run and dagster_run.status in IN_PROGRESS_RUN_STATUSES:
                return AutomationResult(
                    context,
                    context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
                        context.legacy_context.candidate_subset
                    ),
                )
        return AutomationResult(
            context,
            context.asset_graph_view.legacy_get_asset_subset_from_valid_subset(
                context.legacy_context.empty_subset()
            ),
        )
