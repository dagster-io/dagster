from dagster import AssetKey, DagsterInstance, observable_source_asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
    get_auto_observe_run_requests,
    reconcile,
)
from pytest import fixture


def test_single_observable_source_asset_no_auto_observe():
    @observable_source_asset
    def asset1():
        ...

    asset_graph = AssetGraph.from_assets([asset1])

    assert (
        len(
            get_auto_observe_run_requests(
                asset_graph=asset_graph,
                current_timestamp=1000,
                last_observe_request_timestamp_by_asset_key={},
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
            )
        )
        == 0
    )


@fixture
def single_auto_observe_source_asset_graph():
    @observable_source_asset(auto_observe_interval_minutes=30)
    def asset1():
        ...

    asset_graph = AssetGraph.from_assets([asset1])
    return asset_graph


def test_single_observable_source_asset_no_prior_observe_requests(
    single_auto_observe_source_asset_graph,
):
    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_source_asset_graph,
        current_timestamp=1000,
        last_observe_request_timestamp_by_asset_key={},
    )
    assert len(run_requests) == 1
    run_request = run_requests[0]
    assert run_request.asset_selection == [AssetKey("asset1")]


def test_single_observable_source_asset_prior_observe_requests(
    single_auto_observe_source_asset_graph,
):
    last_timestamp = 1000

    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_source_asset_graph,
        current_timestamp=last_timestamp + 30 * 60 + 5,
        last_observe_request_timestamp_by_asset_key={AssetKey("asset1"): last_timestamp},
    )
    assert len(run_requests) == 1
    run_request = run_requests[0]
    assert run_request.asset_selection == [AssetKey("asset1")]


def test_single_observable_source_asset_prior_recent_observe_requests(
    single_auto_observe_source_asset_graph,
):
    last_timestamp = 1000

    run_requests = get_auto_observe_run_requests(
        asset_graph=single_auto_observe_source_asset_graph,
        current_timestamp=last_timestamp + 30 * 60 - 5,
        last_observe_request_timestamp_by_asset_key={AssetKey("asset1"): last_timestamp},
    )
    assert len(run_requests) == 0


def test_reconcile():
    @observable_source_asset(auto_observe_interval_minutes=30)
    def asset1():
        ...

    asset_graph = AssetGraph.from_assets([asset1])
    instance = DagsterInstance.ephemeral()

    run_requests, cursor = reconcile(
        auto_observe=True,
        asset_graph=asset_graph,
        target_asset_keys=set(),
        instance=instance,
        cursor=AssetReconciliationCursor.empty(),
        run_tags={},
    )
    assert len(run_requests) == 1
    assert run_requests[0] is False
    assert cursor.last_observe_request_timestamp_by_asset_key[AssetKey(["asset1"])] > 0
