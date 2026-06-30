"""Unit tests for how declarative automation resolves the asset checks on a run request."""

from datetime import datetime, timezone

import dagster as dg
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.automation_tick_evaluation_context import (
    _any_check_uses_automation_condition,
    _ride_along_check_keys_for_assets,
    build_run_requests,
)
from dagster_shared.utils.warnings import disable_dagster_warnings


def _asset_graph_with_two_checked_assets() -> AssetGraph:
    @dg.asset(check_specs=[dg.AssetCheckSpec(name="check", asset="asset_a")])
    def asset_a() -> dg.MaterializeResult:
        return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    @dg.asset(check_specs=[dg.AssetCheckSpec(name="check", asset="asset_b")])
    def asset_b() -> dg.MaterializeResult:
        return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    return AssetGraph.from_assets([asset_a, asset_b])


def test_ride_along_excludes_checks_targeting_other_assets() -> None:
    # A check that targets `asset_b` must NOT be included in the ride-along set resolved for
    # `asset_a` -- only checks that actually target the selected assets ride along.
    asset_graph = _asset_graph_with_two_checked_assets()

    result = _ride_along_check_keys_for_assets(asset_graph, {dg.AssetKey("asset_a")})

    assert result == {dg.AssetCheckKey(dg.AssetKey("asset_a"), "check")}
    assert dg.AssetCheckKey(dg.AssetKey("asset_b"), "check") not in result


def test_ride_along_excludes_checks_with_automation_condition() -> None:
    # Checks that own an automation condition are not part of the default ride-along set (DA
    # schedules them independently).
    @dg.asset
    def asset_a() -> None: ...

    @dg.asset_check(asset=asset_a, automation_condition=dg.AutomationCondition.eager())
    def conditioned_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=asset_a)
    def unconditioned_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    asset_graph = AssetGraph.from_assets([asset_a, conditioned_check, unconditioned_check])

    result = _ride_along_check_keys_for_assets(asset_graph, {dg.AssetKey("asset_a")})

    assert result == {dg.AssetCheckKey(dg.AssetKey("asset_a"), "unconditioned_check")}


def test_any_check_uses_automation_condition_is_scoped_to_selected_assets() -> None:
    # A conditioned check on `asset_b` must not make `asset_a`'s resolution take the DA path.
    @dg.asset
    def asset_a() -> None: ...

    @dg.asset
    def asset_b() -> None: ...

    @dg.asset_check(asset=asset_b, automation_condition=dg.AutomationCondition.eager())
    def conditioned_check_on_b() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    asset_graph = AssetGraph.from_assets([asset_a, asset_b, conditioned_check_on_b])

    assert not _any_check_uses_automation_condition(asset_graph, {dg.AssetKey("asset_a")})
    assert _any_check_uses_automation_condition(asset_graph, {dg.AssetKey("asset_b")})


def test_partitioned_check_requested_without_its_asset() -> None:
    # A partitioned asset check that owns an automation condition can be requested on a tick where
    # its asset is not. The check is then its own entity subset (keyed on the check, not the
    # asset), so building run requests must read the partition keys off the check subset rather
    # than expanding it into asset partitions, which is undefined for a check key.
    daily = dg.DailyPartitionsDefinition("2020-01-01")

    with disable_dagster_warnings():

        @dg.asset(
            partitions_def=daily,
            check_specs=[
                dg.AssetCheckSpec(
                    name="ratio_check",
                    asset="partitioned_asset",
                    partitions_def=daily,
                    automation_condition=dg.AutomationCondition.eager(),
                )
            ],
        )
        def partitioned_asset() -> dg.MaterializeResult:
            return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    defs = dg.Definitions(assets=[partitioned_asset])
    asset_graph = defs.resolve_asset_graph()
    asset_graph_view = AssetGraphView.for_test(
        defs, effective_dt=datetime(2020, 1, 5, tzinfo=timezone.utc)
    )

    check_key = dg.AssetCheckKey(dg.AssetKey("partitioned_asset"), "ratio_check")
    # only the check is requested this tick -- the asset it checks is not
    check_subset = asset_graph_view.get_subset_from_partition_keys(check_key, daily, {"2020-01-03"})

    run_requests = build_run_requests(
        entity_subsets=[check_subset],
        asset_graph=asset_graph,
        run_tags={},
        emit_backfills=False,
        resolve_check_keys_enabled=True,
    )

    assert len(run_requests) == 1
    run_request = run_requests[0]
    assert run_request.partition_key == "2020-01-03"
    assert run_request.asset_check_keys is not None
    assert list(run_request.asset_check_keys) == [check_key]
    assert not run_request.asset_selection
