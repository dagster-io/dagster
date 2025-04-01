import datetime
import logging
from collections.abc import Mapping, Sequence
from typing import AbstractSet  # noqa: UP035

from dagster import AssetKey, DagsterInstance, observable_source_asset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.automation_tick_evaluation_context import (
    AutomationTickEvaluationContext,
)
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
from dagster._core.definitions.run_request import RunRequest
from pytest import fixture


def get_auto_observe_run_requests(
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float],
    current_timestamp: float,
    asset_graph: BaseAssetGraph,
    run_tags: Mapping[str, str],
    auto_observe_asset_keys: AbstractSet[AssetKey],
) -> Sequence[RunRequest]:
    return AutomationTickEvaluationContext(
        0,
        DagsterInstance.ephemeral(),
        asset_graph,
        AssetDaemonCursor(0, last_observe_request_timestamp_by_asset_key, None, None),
        {},
        run_tags,
        auto_observe_asset_keys,
        AssetSelection.all(),
        logging.getLogger(),
        False,
        None,
        datetime.datetime.fromtimestamp(current_timestamp),
    ).evaluate()[0]


def test_single_observable_source_asset_no_auto_observe():
    @observable_source_asset
    def asset1(): ...

    asset_graph = AssetGraph.from_assets([asset1])

    assert (
        len(
            get_auto_observe_run_requests(
                asset_graph=asset_graph,
                current_timestamp=1000,
                last_observe_request_timestamp_by_asset_key={},
                run_tags={},
                auto_observe_asset_keys=asset_graph.external_asset_keys,
            )
        )
        == 0
    )

    assert (
        len(
            get_auto_observe_run_requests(
                asset_graph=asset_graph,
                current_timestamp=1000,
                last_observe_request_timestamp_by_asset_key={AssetKey("asset1"): 1},
                run_tags={},
                auto_observe_asset_keys=asset_graph.external_asset_keys,
            )
        )
        == 0
    )


@fixture(params=[True, False], ids=["use_external_asset", "use_source_asset"])
def single_auto_observe_asset_graph(request):
    @observable_source_asset(auto_observe_interval_minutes=30)
    def asset1(): ...

    observable = create_external_asset_from_source_asset(asset1) if request.param else asset1
    asset_graph = AssetGraph.from_assets([observable])
    return asset_graph


def test_single_observable_source_asset_no_prior_observe_requests(
    single_auto_observe_asset_graph,
):
    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_asset_graph,
        current_timestamp=1000,
        last_observe_request_timestamp_by_asset_key={},
        run_tags={},
        auto_observe_asset_keys=single_auto_observe_asset_graph.observable_asset_keys,
    )
    assert len(run_requests) == 1
    run_request = run_requests[0]
    assert run_request.asset_selection == [AssetKey("asset1")]


def test_single_observable_source_asset_prior_observe_requests(
    single_auto_observe_asset_graph,
):
    last_timestamp = 1000

    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_asset_graph,
        current_timestamp=last_timestamp + 30 * 60 + 5,
        last_observe_request_timestamp_by_asset_key={AssetKey("asset1"): last_timestamp},
        run_tags={},
        auto_observe_asset_keys=single_auto_observe_asset_graph.observable_asset_keys,
    )
    assert len(run_requests) == 1
    run_request = run_requests[0]
    assert run_request.asset_selection == [AssetKey("asset1")]


def test_single_observable_source_asset_prior_recent_observe_requests(
    single_auto_observe_asset_graph,
):
    last_timestamp = 1000

    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_asset_graph,
        current_timestamp=last_timestamp + 30 * 60 - 5,
        last_observe_request_timestamp_by_asset_key={AssetKey("asset1"): last_timestamp},
        run_tags={},
        auto_observe_asset_keys=single_auto_observe_asset_graph.observable_asset_keys,
    )
    assert len(run_requests) == 0


def test_reconcile() -> None:
    @observable_source_asset(auto_observe_interval_minutes=30)
    def asset1(): ...

    asset_graph = AssetGraph.from_assets([asset1])
    instance = DagsterInstance.ephemeral()

    run_requests, cursor, _ = AutomationTickEvaluationContext(
        evaluation_id=1,
        auto_observe_asset_keys={AssetKey(["asset1"])},
        asset_graph=asset_graph,
        asset_selection=AssetSelection.all(),
        instance=instance,
        cursor=AssetDaemonCursor.empty(),
        materialize_run_tags={},
        emit_backfills=False,
        observe_run_tags={"tag1": "tag_value"},
        logger=logging.getLogger("dagster.amp"),
    ).evaluate()
    assert len(run_requests) == 1
    assert run_requests[0].tags.get("tag1") == "tag_value"
    assert run_requests[0].asset_selection == [AssetKey(["asset1"])]
    assert cursor.last_observe_request_timestamp_by_asset_key[AssetKey(["asset1"])] > 0
