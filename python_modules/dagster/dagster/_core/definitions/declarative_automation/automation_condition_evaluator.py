import logging
from collections import defaultdict
from dataclasses import dataclass, replace
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

from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.events import AssetKey

if TYPE_CHECKING:
    import datetime

    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


@dataclass
class AutomationConditionEvaluator:
    def __init__(
        self,
        *,
        asset_graph: BaseAssetGraph,
        asset_keys: AbstractSet[AssetKey],
        asset_graph_view: AssetGraphView,
        logger: logging.Logger,
        cursor: AssetDaemonCursor,
        data_time_resolver: CachingDataTimeResolver,
        respect_materialization_data_versions: bool,
        # Mapping from run tags to values that should be automatically added run emitted by
        # the declarative scheduling system. This ends up getting sources from places such
        # as https://docs.dagster.io/deployment/dagster-instance#auto-materialize
        # Should this be a supported feature in DS?
        auto_materialize_run_tags: Mapping[str, str],
        request_backfills: bool,
    ):
        self.asset_graph = asset_graph
        self.asset_keys = asset_keys
        self.asset_graph_view = asset_graph_view
        self.logger = logger
        self.cursor = cursor
        self.data_time_resolver = data_time_resolver
        self.respect_materialization_data_versions = respect_materialization_data_versions
        self.auto_materialize_run_tags = auto_materialize_run_tags

        self.current_results_by_key = {}
        self.condition_cursors = []
        self.expected_data_time_mapping = defaultdict()
        self.num_checked_assets = 0
        self.num_asset_keys = len(asset_keys)
        self.request_backfills = request_backfills

        self.legacy_expected_data_time_by_key: Dict[AssetKey, Optional[datetime.datetime]] = {}
        self._execution_set_extras: Dict[AssetKey, List[EntitySubset[AssetKey]]] = defaultdict(list)

    asset_graph: BaseAssetGraph[BaseAssetNode]
    asset_keys: AbstractSet[AssetKey]
    asset_graph_view: AssetGraphView
    current_results_by_key: Dict[AssetKey, AutomationResult]
    num_checked_assets: int
    num_asset_keys: int
    logger: logging.Logger
    cursor: AssetDaemonCursor
    data_time_resolver: CachingDataTimeResolver
    respect_materialization_data_versions: bool
    auto_materialize_run_tags: Mapping[str, str]
    request_backfills: bool

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self.asset_graph_view.get_inner_queryer_for_back_compat()

    @property
    def evaluated_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        return {
            parent
            for asset_key in self.asset_keys
            for parent in self.asset_graph.get(asset_key).parent_keys
        } | self.asset_keys

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

    def evaluate(self) -> Tuple[Iterable[AutomationResult], Iterable[EntitySubset[AssetKey]]]:
        self.prefetch()
        for asset_key in self.asset_graph.toposorted_asset_keys:
            if asset_key not in self.asset_keys:
                continue

            self.num_checked_assets += 1
            self.logger.debug(
                f"Evaluating asset {asset_key.to_user_string()} ({self.num_checked_assets}/{self.num_asset_keys})"
            )

            try:
                self.evaluate_asset(asset_key)
            except Exception as e:
                raise Exception(
                    f"Error while evaluating conditions for asset {asset_key.to_user_string()}"
                ) from e

            result = self.current_results_by_key[asset_key]
            num_requested = result.true_subset.size
            requested_str = ",".join(
                [
                    (ap.partition_key or "No partition")
                    for ap in result.true_subset.expensively_compute_asset_partitions()
                ]
            )
            log_fn = self.logger.info if num_requested > 0 else self.logger.debug
            log_fn(
                f"Asset {asset_key.to_user_string()} evaluation result: {num_requested} "
                f"requested ({requested_str}) "
                f"({format(result.end_timestamp - result.start_timestamp, '.3f')} seconds)"
            )
        return self.current_results_by_key.values(), self._get_entity_subsets()

    def evaluate_asset(self, asset_key: AssetKey) -> None:
        # evaluate the condition of this asset
        context = AutomationContext.create(asset_key=asset_key, evaluator=self)
        result = context.condition.evaluate(context)

        # update dictionaries to keep track of this result
        self.current_results_by_key[asset_key] = result
        self.legacy_expected_data_time_by_key[asset_key] = (
            result.compute_legacy_expected_data_time()
        )

        # handle cases where an entity must be materialized with others
        self._handle_execution_set(result)

    def _handle_execution_set(self, result: AutomationResult[AssetKey]) -> None:
        # if we need to materialize any partitions of a non-subsettable multi-asset, we need to
        # materialize all of them
        asset_key = result.asset_key
        execution_set_keys = self.asset_graph.get(asset_key).execution_set_asset_keys

        if len(execution_set_keys) > 1 and result.true_subset.size > 0:
            for neighbor_key in execution_set_keys:
                self.legacy_expected_data_time_by_key[neighbor_key] = (
                    self.legacy_expected_data_time_by_key[asset_key]
                )

                # make sure that the true_subset of the neighbor is accurate -- when it was
                # evaluated it may have had a different requested subset. however, because
                # all these neighbors must be executed as a unit, we need to union together
                # the subset of all required neighbors
                if neighbor_key in self.current_results_by_key:
                    neighbor_true_subset = replace(
                        result.serializable_evaluation.true_subset, key=neighbor_key
                    )
                    self.current_results_by_key[
                        neighbor_key
                    ].set_internal_serializable_subset_override(neighbor_true_subset)

                extra = self.asset_graph_view.get_subset_from_serializable_subset(
                    SerializableEntitySubset(
                        neighbor_key,
                        result.true_subset.get_internal_value(),
                    )
                )
                if extra:
                    self._execution_set_extras[neighbor_key].append(extra)

    def _get_entity_subsets(self) -> Iterable[EntitySubset[AssetKey]]:
        subsets_by_key = {
            key: result.true_subset for key, result in self.current_results_by_key.items()
        }
        # add in any additional asset partitions we need to request to abide by execution
        # set rules
        for key, extras in self._execution_set_extras.items():
            new_value = subsets_by_key.get(key) or self.asset_graph_view.get_empty_subset(key=key)
            for extra in extras:
                new_value = new_value.compute_union(extra)
            subsets_by_key[key] = new_value

        return subsets_by_key.values()
