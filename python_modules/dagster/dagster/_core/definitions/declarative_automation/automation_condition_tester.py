import datetime
import logging
from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Mapping, Optional, Sequence

import mock
import pendulum

from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetConditionEvaluation,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKeyPartitionKey, AssetMaterialization
from dagster._core.instance import DagsterInstance
from dagster._utils.log import create_console_logger


class AutomationConditionTesterResult:
    def __init__(self, requested_asset_partitions: AbstractSet[AssetKeyPartitionKey]):
        self._requested_asset_partitions = requested_asset_partitions

    @cached_property
    def _requested_partitions_by_asset_key(self) -> Mapping[AssetKey, AbstractSet[Optional[str]]]:
        mapping = defaultdict(set)
        for asset_partition in self._requested_asset_partitions:
            mapping[asset_partition.asset_key].add(asset_partition.partition_key)
        return mapping

    @property
    def total_requested(self) -> int:
        """Returns the total number of asset partitions requested during this evaluation."""
        return len(self._requested_asset_partitions)

    def get_requested_partitions(self, asset_key: AssetKey) -> AbstractSet[Optional[str]]:
        """Returns the specific partition keys requested for the given asset during this evaluation."""
        return self._requested_partitions_by_asset_key[asset_key]

    def get_num_requested(self, asset_key: AssetKey) -> int:
        """Returns the number of asset partitions requested for the given asset during this evaluation."""
        return len(self.get_requested_partitions(asset_key))


class AutomationConditionTester:
    def __init__(
        self,
        defs: Definitions,
        asset_selection: AssetSelection = AssetSelection.all(),
        current_time: Optional[datetime.datetime] = None,
    ):
        self._defs = defs
        self._asset_selection = asset_selection
        self._current_time = current_time or pendulum.now("UTC")
        self._instance = DagsterInstance.ephemeral()
        self._cursor = AssetDaemonCursor.empty()
        self._logger = create_console_logger("dagster.automation", logging.DEBUG)

    def set_current_time(self, dt: datetime.datetime) -> None:
        self._current_time = dt

    def add_materializations(
        self, asset_key: AssetKey, partitions: Optional[Sequence[str]] = None
    ) -> None:
        with mock.patch("time.time", new=lambda: self._current_time.timestamp()):
            for partition in partitions or {None}:
                self._instance.report_runless_asset_event(
                    AssetMaterialization(asset_key=asset_key, partition=partition)
                )

    def evaluate(self) -> AutomationConditionTesterResult:
        """Evaluates the AutomationConditions of all provided assets."""
        asset_graph_view = AssetGraphView.for_test(
            defs=self._defs,
            instance=self._instance,
            effective_dt=self._current_time,
            last_event_id=self._instance.event_log_storage.get_maximum_record_id(),
        )
        asset_graph = self._defs.get_asset_graph()
        data_time_resolver = CachingDataTimeResolver(
            asset_graph_view.get_inner_queryer_for_back_compat()
        )
        evaluator = AutomationConditionEvaluator(
            asset_graph=asset_graph,
            asset_keys=self._asset_selection.resolve(asset_graph),
            asset_graph_view=asset_graph_view,
            logger=self._logger,
            cursor=self._cursor,
            data_time_resolver=data_time_resolver,
            respect_materialization_data_versions=False,
            auto_materialize_run_tags={},
        )
        results, requested_asset_partitions = evaluator.evaluate()
        self._cursor = AssetDaemonCursor(
            evaluation_id=0,
            last_observe_request_timestamp_by_asset_key={},
            previous_evaluation_state=None,
            previous_condition_cursors=[result.get_new_cursor() for result in results],
        )

        for result in results:
            self._logger.info(f"Evaluation of {result.asset_key}:")
            self._log_evaluation(result.serializable_evaluation)

        return AutomationConditionTesterResult(requested_asset_partitions)

    def _log_evaluation(self, evaluation: AssetConditionEvaluation, depth: int = 1) -> None:
        msg = "  " * depth
        msg += f"{evaluation.condition_snapshot.description} "
        msg += f"({evaluation.true_subset.size} true) "
        msg += (
            f"({(evaluation.end_timestamp or 0) - (evaluation.start_timestamp or 0):.2f} seconds)"
        )
        self._logger.info(msg)
        for child in evaluation.child_evaluations:
            self._log_evaluation(child, depth + 1)
