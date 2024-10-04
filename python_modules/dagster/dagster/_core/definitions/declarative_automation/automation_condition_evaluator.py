import datetime
import logging
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.events import AssetKey
from dagster._core.instance import DagsterInstance
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class AutomationConditionEvaluator:
    def __init__(
        self,
        *,
        entity_keys: AbstractSet[EntityKey],
        instance: DagsterInstance,
        asset_graph: BaseAssetGraph,
        cursor: AssetDaemonCursor,
        allow_backfills: bool,
        default_condition: Optional[AutomationCondition] = None,
        evaluation_time: Optional[datetime.datetime] = None,
        logger: logging.Logger = logging.getLogger("dagster.automation"),
    ):
        self.entity_keys = entity_keys
        self.asset_graph_view = AssetGraphView(
            temporal_context=TemporalContext(
                effective_dt=evaluation_time or get_current_datetime(),
                last_event_id=instance.event_log_storage.get_maximum_record_id(),
            ),
            instance=instance,
            asset_graph=asset_graph,
        )
        self.logger = logger
        self.cursor = cursor
        self.default_condition = default_condition

        self.current_results_by_key: Dict[EntityKey, AutomationResult] = {}
        self.condition_cursors = []
        self.expected_data_time_mapping = defaultdict()

        _instance = self.asset_graph_view.instance
        self.legacy_auto_materialize_run_tags: Mapping[str, str] = (
            _instance.auto_materialize_run_tags
        )
        self.legacy_respect_materialization_data_versions = (
            _instance.auto_materialize_respect_materialization_data_versions
        )
        self.allow_backfills = allow_backfills or _instance.da_request_backfills()

        self.legacy_expected_data_time_by_key: Dict[AssetKey, Optional[datetime.datetime]] = {}
        self.legacy_data_time_resolver = CachingDataTimeResolver(self.instance_queryer)

        self._execution_set_extras: Dict[EntityKey, List[EntitySubset[EntityKey]]] = defaultdict(
            list
        )

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self.asset_graph_view.get_inner_queryer_for_back_compat()

    @property
    def evaluation_time(self) -> datetime.datetime:
        return self.asset_graph_view.effective_dt

    @property
    def asset_graph(self) -> "BaseAssetGraph[BaseAssetNode]":
        return self.asset_graph_view.asset_graph

    @property
    def evaluated_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        asset_keys = {ek for ek in self.entity_keys if isinstance(ek, AssetKey)}
        return {
            parent for ek in asset_keys for parent in self.asset_graph.get(ek).parent_keys
        } | asset_keys

    @property
    def asset_records_to_prefetch(self) -> Sequence[AssetKey]:
        return [key for key in self.evaluated_asset_keys_and_parents if self.asset_graph.has(key)]

    def prefetch(self) -> None:
        """Pre-populate the cached values here to avoid situations in which the new latest_storage_id
        value is calculated using information that comes in after the set of asset partitions with
        new parent materializations is calculated, as this can result in materializations being
        ignored if they happen between the two calculations.
        """
        self.logger.info(
            f"Prefetching asset records for {len(self.asset_records_to_prefetch)} records."
        )
        self.instance_queryer.prefetch_asset_records(self.asset_records_to_prefetch)
        self.logger.info("Done prefetching asset records.")

    def evaluate(self) -> Tuple[Sequence[AutomationResult], Sequence[EntitySubset[EntityKey]]]:
        self.prefetch()
        num_conditions = len(self.entity_keys)
        num_evaluated = 0
        for entity_key in self.asset_graph.toposorted_entity_keys:
            if entity_key not in self.entity_keys:
                continue

            self.logger.debug(
                f"Evaluating {entity_key.to_user_string()} ({num_evaluated+1}/{num_conditions})"
            )

            try:
                self.evaluate_entity(entity_key)
            except Exception as e:
                raise Exception(
                    f"Error while evaluating conditions for {entity_key.to_user_string()}"
                ) from e

            result = self.current_results_by_key[entity_key]
            num_requested = result.true_subset.size
            if result.true_subset.is_partitioned:
                requested_str = ",".join(result.true_subset.expensively_compute_partition_keys())
            else:
                requested_str = "(no partition)"
            log_fn = self.logger.info if num_requested > 0 else self.logger.debug
            log_fn(
                f"{entity_key.to_user_string()} evaluation result: {num_requested} "
                f"requested ({requested_str}) "
                f"({format(result.end_timestamp - result.start_timestamp, '.3f')} seconds)"
            )
            num_evaluated += 1
        return list(self.current_results_by_key.values()), list(self._get_entity_subsets())

    def evaluate_entity(self, key: EntityKey) -> None:
        # evaluate the condition of this asset
        context = AutomationContext.create(key=key, evaluator=self)
        result = context.condition.evaluate(context)

        # update dictionaries to keep track of this result
        self.current_results_by_key[key] = result

        if isinstance(key, AssetKey):
            self.legacy_expected_data_time_by_key[key] = result.compute_legacy_expected_data_time()
            # handle cases where an entity must be materialized with others
            self._handle_execution_set(result)

    def _handle_execution_set(self, result: AutomationResult[AssetKey]) -> None:
        # if we need to materialize any partitions of a non-subsettable multi-asset, we need to
        # materialize all of them
        asset_key = result.key
        execution_set_keys = self.asset_graph.get(asset_key).execution_set_entity_keys

        if len(execution_set_keys) > 1 and result.true_subset.size > 0:
            for neighbor_key in execution_set_keys:
                if isinstance(neighbor_key, AssetKey):
                    self.legacy_expected_data_time_by_key[neighbor_key] = (
                        self.legacy_expected_data_time_by_key[asset_key]
                    )

                # make sure that the true_subset of the neighbor is accurate -- when it was
                # evaluated it may have had a different requested subset. however, because
                # all these neighbors must be executed as a unit, we need to union together
                # the subset of all required neighbors
                neighbor_true_subset = result.true_subset.compute_mapped_subset(neighbor_key)
                if neighbor_key in self.current_results_by_key:
                    self.current_results_by_key[
                        neighbor_key
                    ].set_internal_serializable_subset_override(
                        neighbor_true_subset.convert_to_serializable_subset()
                    )

                self._execution_set_extras[neighbor_key].append(neighbor_true_subset)

    def _get_entity_subsets(self) -> Iterable[EntitySubset[EntityKey]]:
        subsets_by_key = {
            key: result.true_subset
            for key, result in self.current_results_by_key.items()
            if not result.true_subset.is_empty
        }
        # add in any additional asset partitions we need to request to abide by execution
        # set rules
        for key, extras in self._execution_set_extras.items():
            new_value = subsets_by_key.get(key) or self.asset_graph_view.get_empty_subset(key=key)
            for extra in extras:
                new_value = new_value.compute_union(extra)
            subsets_by_key[key] = new_value

        return subsets_by_key.values()
