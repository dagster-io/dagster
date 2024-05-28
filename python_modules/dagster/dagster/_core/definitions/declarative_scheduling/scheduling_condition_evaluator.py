import dataclasses
import datetime
import logging
import time
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_scheduling.scheduling_context import (
    SchedulingContext,
)
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    SchedulingEvaluationInfo,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from ..asset_daemon_cursor import AssetDaemonCursor
from ..base_asset_graph import BaseAssetGraph
from ..freshness_based_auto_materialize import get_expected_data_time_for_asset_key
from .legacy.legacy_context import (
    LegacyRuleEvaluationContext,
)
from .serialized_objects import (
    AssetConditionEvaluationState,
)

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import (
        CachingInstanceQueryer,
    )

from dataclasses import dataclass


@dataclass
class SchedulingConditionEvaluator:
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

        self.evaluation_state_by_key = {}
        self.current_evaluation_info_by_key = {}
        self.expected_data_time_mapping = defaultdict()
        self.to_request = set()
        self.num_checked_assets = 0
        self.num_asset_keys = len(asset_keys)

    asset_graph: BaseAssetGraph
    asset_keys: AbstractSet[AssetKey]
    asset_graph_view: AssetGraphView
    evaluation_state_by_key: Dict[AssetKey, AssetConditionEvaluationState]
    current_evaluation_info_by_key: Dict[AssetKey, SchedulingEvaluationInfo]
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

    def evaluate(
        self,
    ) -> Tuple[Sequence[AssetConditionEvaluationState], AbstractSet[AssetKeyPartitionKey]]:
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
                (evaluation_state, expected_data_time) = self.evaluate_asset(
                    asset_key,
                    self.evaluation_state_by_key,
                    self.expected_data_time_mapping,
                    self.current_evaluation_info_by_key,
                )
            except Exception as e:
                raise Exception(
                    f"Error while evaluating conditions for asset {asset_key.to_user_string()}"
                ) from e

            num_requested = evaluation_state.true_subset.size
            log_fn = self.logger.info if num_requested > 0 else self.logger.debug

            to_request_asset_partitions = evaluation_state.true_subset.asset_partitions
            to_request_str = ",".join(
                [(ap.partition_key or "No partition") for ap in to_request_asset_partitions]
            )
            self.to_request |= to_request_asset_partitions

            log_fn(
                f"Asset {asset_key.to_user_string()} evaluation result: {num_requested}"
                f" requested ({to_request_str}) ({format(time.time()-start_time, '.3f')} seconds)"
            )

            self.evaluation_state_by_key[asset_key] = evaluation_state
            self.current_evaluation_info_by_key[asset_key] = (
                SchedulingEvaluationInfo.from_asset_condition_evaluation_state(
                    self.asset_graph_view, evaluation_state
                )
            )
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
                    if neighbor_key in self.evaluation_state_by_key:
                        neighbor_evaluation_state = self.evaluation_state_by_key[neighbor_key]
                        self.evaluation_state_by_key[neighbor_key] = dataclasses.replace(
                            neighbor_evaluation_state,
                            previous_evaluation=neighbor_evaluation_state.previous_evaluation.copy(
                                update={
                                    "true_subset": neighbor_evaluation_state.true_subset.copy(
                                        update={"asset_key": neighbor_key}
                                    )
                                }
                            ),
                        )
                    self.to_request |= {
                        ap._replace(asset_key=neighbor_key)
                        for ap in evaluation_state.true_subset.asset_partitions
                    }

        return (list(self.evaluation_state_by_key.values()), self.to_request)

    def evaluate_asset(
        self,
        asset_key: AssetKey,
        evaluation_state_by_key: Mapping[AssetKey, AssetConditionEvaluationState],
        expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
        current_evaluation_info_by_key: Mapping[AssetKey, SchedulingEvaluationInfo],
    ) -> Tuple[AssetConditionEvaluationState, Optional[datetime.datetime]]:
        """Evaluates the auto materialize policy of a given asset key.

        Params:
            - asset_key: The asset key to evaluate.
            - will_materialize_mapping: A mapping of AssetKey to the set of AssetKeyPartitionKeys
                that will be materialized this tick. As this function is called in topological order,
                this mapping will contain the expected materializations of all upstream assets.
            - expected_data_time_mapping: A mapping of AssetKey to the expected data time of the
                asset after this tick. As this function is called in topological order, this mapping
                will contain the expected data times of all upstream assets.

        """
        # convert the legacy AutoMaterializePolicy to an Evaluator
        asset_condition = check.not_none(
            self.asset_graph.get(asset_key).auto_materialize_policy
        ).to_scheduling_condition()

        previous_evaluation_state = self.cursor.get_previous_evaluation_state(asset_key)

        legacy_context = LegacyRuleEvaluationContext.create(
            asset_key=asset_key,
            previous_evaluation_state=previous_evaluation_state,
            condition=asset_condition,
            instance_queryer=self.instance_queryer,
            data_time_resolver=self.data_time_resolver,
            evaluation_state_by_key=evaluation_state_by_key,
            expected_data_time_mapping=expected_data_time_mapping,
            respect_materialization_data_versions=self.respect_materialization_data_versions,
            auto_materialize_run_tags=self.auto_materialize_run_tags,
            logger=self.logger,
        )

        context = SchedulingContext.create(
            asset_key=asset_key,
            asset_graph_view=self.asset_graph_view,
            logger=self.logger,
            current_tick_evaluation_info_by_key=current_evaluation_info_by_key,
            previous_evaluation_info=SchedulingEvaluationInfo.from_asset_condition_evaluation_state(
                self.asset_graph_view, previous_evaluation_state
            )
            if previous_evaluation_state
            else None,
            legacy_context=legacy_context,
        )

        result = asset_condition.evaluate(context)

        expected_data_time = get_expected_data_time_for_asset_key(
            legacy_context, will_materialize=result.true_subset.size > 0
        )
        return AssetConditionEvaluationState.create(context, result), expected_data_time
