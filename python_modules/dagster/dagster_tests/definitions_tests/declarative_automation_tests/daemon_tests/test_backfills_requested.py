from unittest import mock

from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey

from dagster_tests.definitions_tests.declarative_automation_tests.daemon_tests.test_asset_daemon import (
    get_daemon_instance,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.asset_daemon_scenario import (
    AssetDaemonScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    run_request,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    daily_partitions_def,
    hourly_partitions_def,
    two_assets_in_sequence,
    two_disconnected_graphs,
    two_partitions_def,
)


@mock.patch(
    "dagster_tests.definitions_tests.declarative_automation_tests.daemon_tests.test_asset_daemon.DagsterInstance.da_request_backfills",
    return_value=True,
)
def test_simple_conditions_with_backfills(mock_da_request_backfills) -> None:
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"use_sensors": False}}
    ) as instance:
        state = (
            AssetDaemonScenarioState(
                two_assets_in_sequence.with_asset_properties(
                    keys=["B"],
                    automation_condition=AutomationCondition.any_deps_match(
                        AutomationCondition.newly_updated()
                    ),
                ),
                request_backfills=True,
                instance=instance,
            )
            .with_asset_properties(partitions_def=hourly_partitions_def)
            .with_current_time("2020-02-02T01:05:00")
        )

        # parent hasn't updated yet
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # update A with an old partition, should cause B to materialize
        state = state.with_runs(run_request("A", "2019-07-05-00:00"))
        state = state.with_runs(run_request("A", "2019-07-05-01:00"))
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 1
        assert new_run_requests[0].requires_backfill_daemon()

        # materialize the latest partition of A, B should be requested again
        state = state.with_runs(run_request("A", "2020-02-02-00:00"))
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 1
        # backfill daemon not required
        assert not new_run_requests[0].requires_backfill_daemon()

        # now B has been materialized, so don't execute again
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # new partition comes into being, parent hasn't been materialized yet
        state = state.with_current_time_advanced(hours=1)
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # parent gets materialized, B requested
        state = state.with_runs(run_request("A", "2020-02-02-01:00"))
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 1
        # but it fails
        state = state.with_failed_run_for_asset("B", "2020-02-02-01:00")

        # B does not get immediately requested again
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0


@mock.patch(
    "dagster_tests.definitions_tests.declarative_automation_tests.daemon_tests.test_asset_daemon.DagsterInstance.da_request_backfills",
    return_value=True,
)
def test_disconnected_graphs_backfill(mock_da_request_backfills) -> None:
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"use_sensors": False}}
    ) as instance:
        state = (
            AssetDaemonScenarioState(
                two_disconnected_graphs.with_asset_properties(
                    keys=["B", "D"],
                    automation_condition=AutomationCondition.any_deps_match(
                        AutomationCondition.newly_updated()
                    ),
                ),
                request_backfills=True,
                instance=instance,
            )
            .with_asset_properties(keys=["A", "B"], partitions_def=daily_partitions_def)
            .with_asset_properties(keys=["C", "D"], partitions_def=two_partitions_def)
            .with_current_time("2020-02-02T01:05:00")
        )

        # parent hasn't updated yet
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # A updated, now can execute B, but not D
        state = state.with_runs(run_request("A", "2020-02-01"))
        state = state.with_runs(run_request("A", "2020-01-30"))
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 1
        assert new_run_requests[0].requires_backfill_daemon()
        assert new_run_requests[0].asset_graph_subset
        assert new_run_requests[0].asset_graph_subset.asset_keys == {AssetKey("B")}
        state = state.with_runs(
            *(
                run_request(ak, pk)
                for ak, pk in new_run_requests[0].asset_graph_subset.iterate_asset_partitions()
            )
        )

        # now B has been materialized, so don't execute again
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # new partition comes into being, parent hasn't been materialized yet
        state = state.with_current_time_advanced(days=1)
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 0

        # both A and C get materialized, B and D requested in the same backfill
        state = state.with_runs(
            run_request("A", "2020-01-30"),
            run_request("A", "2020-02-02"),
            run_request("C", "1"),
            run_request("C", "2"),
        )
        state, new_run_requests = state.evaluate_tick_daemon()
        assert len(new_run_requests) == 1
        assert new_run_requests[0].requires_backfill_daemon()
        assert new_run_requests[0].asset_graph_subset and new_run_requests[
            0
        ].asset_graph_subset.asset_keys == {AssetKey("B"), AssetKey("D")}
