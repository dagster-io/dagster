from datetime import datetime, timezone

from dagster import AutomationCondition
from dagster._core.definitions.time_window_partitions import TimeWindow

from dagster_tests.definitions_tests.auto_materialize_tests.base_scenario import run_request

from ..scenario_specs import (
    daily_partitions_def,
    hourly_partitions_def,
    two_assets_depend_on_one,
    two_assets_in_sequence,
)
from .asset_condition_scenario import AutomationConditionScenarioState


def test_simple_eager_conditions_with_backfills() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_in_sequence,
            automation_condition=AutomationCondition.eager(),
            ensure_empty_result=False,
            request_backfills=True,
        )
        .with_asset_properties(partitions_def=hourly_partitions_def)
        .with_current_time("2020-02-02T01:05:00")
    )

    # parent hasn't updated yet
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 0

    # historical parent updated, doesn't matter
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 0

    # latest parent updated, now can execute
    state = state.with_runs(run_request("A", "2020-02-02-00:00"))
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 1
    assert new_run_requests[0].requires_backfill_daemon()
    state = state.with_runs(
        *(
            run_request(ak, pk)
            for ak, pk in new_run_requests[0].asset_graph_subset.iterate_asset_partitions()
        )
    )

    # now B has been materialized, so don't execute again
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 0

    # new partition comes into being, parent hasn't been materialized yet
    state = state.with_current_time_advanced(hours=1)
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 0

    # parent gets materialized, B requested
    state = state.with_runs(run_request("A", "2020-02-02-01:00"))
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 1
    # but it fails
    state = state.with_failed_run_for_asset("B", "2020-02-02-01:00")

    # B does not get immediately requested again
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B"])
    assert len(new_run_requests) == 0


def test_multiple_partitions_defs_backfill() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_depend_on_one,
            automation_condition=AutomationCondition.eager(),
            ensure_empty_result=False,
            request_backfills=True,
        )
        .with_asset_properties(keys=["A"], partitions_def=hourly_partitions_def)
        .with_asset_properties(keys=["B", "C"], partitions_def=daily_partitions_def)
        .with_current_time("2020-02-02T01:05:00")
    )

    # parent hasn't updated yet
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 0

    # historical parent updated, doesn't matter
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 0

    # latest parent updated, now can execute
    state = state.with_runs(
        *(
            run_request("A", pk)
            for pk in hourly_partitions_def.get_partition_keys_in_time_window(
                TimeWindow(
                    start=datetime(2020, 2, 1, 0, 0, tzinfo=timezone.utc),
                    end=datetime(2020, 2, 2, 1, 0, tzinfo=timezone.utc),
                )
            )
        )
    )
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 1
    assert new_run_requests[0].requires_backfill_daemon()
    state = state.with_runs(
        *(
            run_request(ak, pk)
            for ak, pk in new_run_requests[0].asset_graph_subset.iterate_asset_partitions()
        )
    )

    # now B has been materialized, so don't execute again
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 0

    # new partition comes into being, parent hasn't been materialized yet
    state = state.with_current_time_advanced(days=1)
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 0

    # parent gets materialized, B and C requested
    state = state.with_runs(
        *(
            run_request("A", pk)
            for pk in hourly_partitions_def.get_partition_keys_in_time_window(
                TimeWindow(
                    start=datetime(2020, 2, 2, 0, 0, tzinfo=timezone.utc),
                    end=datetime(2020, 2, 3, 1, 0, tzinfo=timezone.utc),
                )
            )
        )
    )
    new_run_requests, _, _ = state.evaluate_daemon_tick(["B", "C"])
    assert len(new_run_requests) == 1
    assert new_run_requests[0].requires_backfill_daemon()
