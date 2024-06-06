import datetime
import logging
import time
from collections import defaultdict
from typing import TYPE_CHECKING, AbstractSet, Dict, Mapping, Optional, Sequence, Set, Tuple

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from ..asset_daemon_cursor import AssetDaemonCursor
from ..base_asset_graph import BaseAssetGraph
from ..freshness_based_auto_materialize import get_expected_data_time_for_asset_key
from .legacy.legacy_context import LegacyRuleEvaluationContext

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from dataclasses import dataclass


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
        self.to_request = set()
        self.num_checked_assets = 0
        self.num_asset_keys = len(asset_keys)

    asset_graph: BaseAssetGraph
    asset_keys: AbstractSet[AssetKey]
    asset_graph_view: AssetGraphView
    current_results_by_key: Dict[AssetKey, AutomationResult]
    expected_data_time_mapping: Dict[AssetKey, Optional[datetime.datetime]]
    to_request: Set[AssetKeyPartitionKey]
    num_checked_assets: int
    num_asset_keys: int
    logger: logging.Logger
    cursor: AssetDaemonCursor
    data_time_resolver: CachingDataTimeResolver
    respect_materialization_data_versions: bool
    auto_materialize_run_tags: Mapping[str, str]

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

    def evaluate(self) -> Tuple[Sequence[AutomationResult], AbstractSet[AssetKeyPartitionKey]]:
        self.prefetch()
        for asset_key in self.asset_graph.toposorted_asset_keys:
            # an asset may have already been visited if it was part of a non-subsettable multi-asset
            if asset_key not in self.asset_keys:
                continue

            self.num_checked_assets = self.num_checked_assets + 1
            start_time = time.time()
            self.logger.debug(
                "Evaluating asset"
                f" {asset_key.to_user_string()} ({self.num_checked_assets}/{self.num_asset_keys})"
            )

            try:
                (result, expected_data_time) = self.evaluate_asset(
                    asset_key, self.expected_data_time_mapping, self.current_results_by_key
                )
            except Exception as e:
                raise Exception(
                    f"Error while evaluating conditions for asset {asset_key.to_user_string()}"
                ) from e

            num_requested = result.true_subset.size
            log_fn = self.logger.info if num_requested > 0 else self.logger.debug

            to_request_asset_partitions = result.true_subset.asset_partitions
            to_request_str = ",".join(
                [(ap.partition_key or "No partition") for ap in to_request_asset_partitions]
            )
            self.to_request |= to_request_asset_partitions

            log_fn(
                f"Asset {asset_key.to_user_string()} evaluation result: {num_requested}"
                f" requested ({to_request_str}) ({format(time.time()-start_time, '.3f')} seconds)"
            )

            self.current_results_by_key[asset_key] = result
            self.expected_data_time_mapping[asset_key] = expected_data_time

            # if we need to materialize any partitions of a non-subsettable multi-asset, we need to
            # materialize all of them
            execution_set_keys = self.asset_graph.get(asset_key).execution_set_asset_keys
            if len(execution_set_keys) > 1 and num_requested > 0:
                for neighbor_key in execution_set_keys:
                    self.expected_data_time_mapping[neighbor_key] = expected_data_time

                    # make sure that the true_subset of the neighbor is accurate -- when it was
                    # evaluated it may have had a different requested AssetSubset. however, because
                    # all these neighbors must be executed as a unit, we need to union together
                    # the subset of all required neighbors
                    if neighbor_key in self.current_results_by_key:
                        neighbor_result = self.current_results_by_key[neighbor_key]
                        neighbor_true_subset = result.serializable_evaluation.true_subset._replace(
                            asset_key=neighbor_key
                        )
                        neighbor_evaluation = result.serializable_evaluation._replace(
                            true_subset=neighbor_true_subset
                        )
                        self.current_results_by_key[neighbor_key] = neighbor_result._replace(
                            serializable_evaluation=neighbor_evaluation
                        )
                    self.to_request |= {
                        ap._replace(asset_key=neighbor_key)
                        for ap in result.true_subset.asset_partitions
                    }

        return list(self.current_results_by_key.values()), self.to_request

    def evaluate_asset(
        self,
        asset_key: AssetKey,
        expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
        current_results_by_key: Mapping[AssetKey, AutomationResult],
    ) -> Tuple[AutomationResult, Optional[datetime.datetime]]:
        """Evaluates the auto materialize policy of a given asset key."""
        # convert the legacy AutoMaterializePolicy to an Evaluator
        asset_condition = check.not_none(
            self.asset_graph.get(asset_key).auto_materialize_policy
        ).to_automation_condition()

        legacy_context = LegacyRuleEvaluationContext.create(
            asset_key=asset_key,
            cursor=self.cursor.get_previous_condition_cursor(asset_key),
            condition=asset_condition,
            instance_queryer=self.instance_queryer,
            data_time_resolver=self.data_time_resolver,
            current_results_by_key=current_results_by_key,
            expected_data_time_mapping=expected_data_time_mapping,
            respect_materialization_data_versions=self.respect_materialization_data_versions,
            auto_materialize_run_tags=self.auto_materialize_run_tags,
            logger=self.logger,
        )

        context = AutomationContext.create(
            asset_key=asset_key,
            asset_graph_view=self.asset_graph_view,
            logger=self.logger,
            current_tick_results_by_key=current_results_by_key,
            condition_cursor=self.cursor.get_previous_condition_cursor(asset_key),
            legacy_context=legacy_context,
        )

        result = asset_condition.evaluate(context)
        expected_data_time = get_expected_data_time_for_asset_key(
            legacy_context, will_materialize=result.true_subset.size > 0
        )
        return result, expected_data_time
