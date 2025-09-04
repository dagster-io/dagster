import datetime
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property
from typing import AbstractSet, Optional, Union  # noqa: UP035

from dagster_shared.serdes import deserialize_value, serialize_value

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.instance import DagsterInstance


class EvaluateAutomationConditionsResult:
    def __init__(
        self,
        cursor: AssetDaemonCursor,
        results: Iterable[AutomationResult],
        requested_subsets: Iterable[EntitySubset],
        partition_loading_context: PartitionLoadingContext,
    ):
        self._requested_subsets = requested_subsets
        self._requested_asset_partitions = set().union(
            *(
                subset.expensively_compute_asset_partitions()
                for subset in requested_subsets
                if isinstance(subset.key, AssetKey)
            )
        )
        self.cursor = cursor
        self.results = list(results)
        self._partition_loading_context = partition_loading_context

    @cached_property
    def _requested_partitions_by_asset_key(self) -> Mapping[AssetKey, AbstractSet[Optional[str]]]:
        mapping = defaultdict(set)
        for asset_partition in self._requested_asset_partitions:
            mapping[asset_partition.asset_key].add(asset_partition.partition_key)
        return mapping

    @property
    def total_requested(self) -> int:
        """Returns the total number of asset partitions requested during this evaluation."""
        with partition_loading_context(new_ctx=self._partition_loading_context):
            return sum(r.true_subset.size for r in self.results)

    def get_requested_partitions(self, asset_key: AssetKey) -> AbstractSet[Optional[str]]:
        """Returns the specific partition keys requested for the given asset during this evaluation."""
        return self._requested_partitions_by_asset_key[asset_key]

    def get_num_requested(self, asset_key: AssetKey) -> int:
        """Returns the number of asset partitions requested for the given asset during this evaluation."""
        return len(self.get_requested_partitions(asset_key))


def evaluate_automation_conditions(
    defs: Union[Definitions, Sequence[AssetsDefinition]],
    instance: DagsterInstance,
    asset_selection: Optional[AssetSelection] = None,
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
            The selection of assets within defs to evaluate against. Defaults to all assets.
        evaluation_time (Optional[datetime.datetime]):
            The time to use for the evaluation. Defaults to the true current time.
        cursor (Optional[AssetDaemonCursor]):
            The cursor for the computation. If you are evaluating multiple ticks within a test, this
            value should be supplied from the `cursor` property of the returned `result` object.
        request_backfills (bool): Whether to evaluate the automation conditions under the condition of DA requesting backfills. Defaults to False.

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

    if asset_selection is None:
        asset_selection = (
            AssetSelection.all(include_sources=True) | AssetSelection.all_asset_checks()
        )

    asset_graph = defs.resolve_asset_graph()

    # round-trip the provided cursor to simulate actual usage
    cursor = (
        deserialize_value(serialize_value(cursor), AssetDaemonCursor)
        if cursor
        else AssetDaemonCursor.empty()
    )
    evaluator = AutomationConditionEvaluator(
        asset_graph=asset_graph,
        instance=instance,
        entity_keys={
            key
            for key in asset_selection.resolve(asset_graph)
            | asset_selection.resolve_checks(asset_graph)
            if asset_graph.get(key).automation_condition is not None
        },
        evaluation_time=evaluation_time,
        emit_backfills=False,
        logger=logging.getLogger("dagster.automation_condition_tester"),
        cursor=cursor,
    )
    results, requested_subsets = evaluator.evaluate()
    with partition_loading_context(
        effective_dt=evaluation_time, dynamic_partitions_store=instance
    ) as ctx:
        new_cursor = cursor.with_updates(
            evaluation_timestamp=(evaluation_time or datetime.datetime.now()).timestamp(),
            newly_observe_requested_asset_keys=[],
            evaluation_id=cursor.evaluation_id + 1,
            condition_cursors=[result.get_new_cursor() for result in results],
            asset_graph=asset_graph,
        )

        return EvaluateAutomationConditionsResult(
            cursor=new_cursor,
            requested_subsets=requested_subsets,
            results=results,
            partition_loading_context=ctx,
        )
