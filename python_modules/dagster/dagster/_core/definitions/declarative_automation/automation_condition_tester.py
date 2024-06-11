import datetime
import logging
from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, Mapping, Optional, Sequence, Union

from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.instance import DagsterInstance
from dagster._time import get_current_datetime


class EvaluateAutomationConditionsResult:
    def __init__(
        self,
        requested_asset_partitions: AbstractSet[AssetKeyPartitionKey],
        cursor: AssetDaemonCursor,
    ):
        self._requested_asset_partitions = requested_asset_partitions
        self.cursor = cursor

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


def evaluate_automation_conditions(
    defs: Union[Definitions, Sequence[AssetsDefinition]],
    instance: DagsterInstance,
    asset_selection: AssetSelection = AssetSelection.all(),
    evaluation_time: Optional[datetime.datetime] = None,
    cursor: Optional[AssetDaemonCursor] = None,
) -> EvaluateAutomationConditionsResult:
    """Evaluates the AutomationConditions of the provided assets, returning the results. Intended
    for use in unit tests.

    Params:
        defs (Union[Definitions, Sequence[AssetsDefinitions]]):
            The definitions to evaluate the conditions of.
        instance (DagsterInstance):
            The instance to evaluate against.
        asset_selection (AssetSelection):
            The selection of assets within defs to evaluate against. Defaults to AssetSelection.all()
        evaluation_time (Optional[datetime.datetime]):
            The time to use for the evaluation. Defaults to the true current time.
        cursor (Optional[AssetDaemonCursor]):
            The cursor for the computation. If you are evaluating multiple ticks within a test, this
            value should be supplied from the `cursor` property of the returned `result` object.

    Examples:
         .. code-block:: python

            from dagster import DagsterInstance, evaluate_automation_conditions

            from my_proj import defs

            def test_my_automation_conditions() -> None:

                instance = DagsterInstance.ephemeral()

                # asset starts off as missing, expect it to be requested
                result = evaluate_automation_conditions(defs, instance)
                assert result.total_requested == 1

                # don't re-request the same asset
                result = evaluate_automation_conditions(defs, instance, cursor=cursor)
                assert result.total_requested == 0


            from dagster import AssetExecutionContext
            from dagster_dbt import DbtCliResource, dbt_assets


            @dbt_assets(manifest=Path("target", "manifest.json"))
            def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                yield from dbt.cli(["build"], context=context).stream()
    """
    if not isinstance(defs, Definitions):
        defs = Definitions(assets=defs)

    asset_graph_view = AssetGraphView.for_test(
        defs=defs,
        instance=instance,
        effective_dt=evaluation_time or get_current_datetime(),
        last_event_id=instance.event_log_storage.get_maximum_record_id(),
    )
    asset_graph = defs.get_asset_graph()
    data_time_resolver = CachingDataTimeResolver(
        asset_graph_view.get_inner_queryer_for_back_compat()
    )
    evaluator = AutomationConditionEvaluator(
        asset_graph=asset_graph,
        asset_keys=asset_selection.resolve(asset_graph),
        asset_graph_view=asset_graph_view,
        logger=logging.getLogger("dagster.automation_condition_tester"),
        cursor=cursor or AssetDaemonCursor.empty(),
        data_time_resolver=data_time_resolver,
        respect_materialization_data_versions=False,
        auto_materialize_run_tags={},
    )
    results, requested_asset_partitions = evaluator.evaluate()
    cursor = AssetDaemonCursor(
        evaluation_id=0,
        last_observe_request_timestamp_by_asset_key={},
        previous_evaluation_state=None,
        previous_condition_cursors=[result.get_new_cursor() for result in results],
    )

    return EvaluateAutomationConditionsResult(
        cursor=cursor,
        requested_asset_partitions=requested_asset_partitions,
    )
