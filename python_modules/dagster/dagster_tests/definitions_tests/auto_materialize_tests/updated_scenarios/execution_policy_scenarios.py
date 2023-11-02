import pytest
from dagster._core.definitions.auto_execution_policy import AutoExecutionPolicy

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
    day_partition_key,
)
from ..base_scenario import run_request
from .asset_daemon_scenario_states import (
    daily_partitions_def,
    one_asset_depends_on_two,
    time_partitions_start,
    two_partitions_def,
)

scenarios = [
    AssetDaemonScenario(
        id="test_unconditional_parent_updated",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            partitions_def=two_partitions_def
        ).with_asset_properties(
            keys=["C"],
            # materialize if parent is updated (no matter what)
            auto_materialize_policy=AutoExecutionPolicy.parent_updated(),
        ),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("A", partition_key="1"))
        .evaluate_tick()
        # can materialize even though B is missing
        .assert_requested_runs(
            run_request("C", partition_key="1"),
        )
        .with_runs(run_request("B", partition_key="1"))
        # can materialize again now
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", partition_key="1"),
        ),
    ),
    AssetDaemonScenario(
        id="test_parent_updated_and_parent_not_missing",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            partitions_def=two_partitions_def
        ).with_asset_properties(
            keys=["C"],
            # materialize if parent is updated and no parents are missing
            auto_materialize_policy=AutoExecutionPolicy.parent_updated()
            & ~AutoExecutionPolicy.parent_missing(),
        ),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("A", partition_key="1"))
        .evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("B", partition_key="1"))
        # now both parents are materialized, so we should get a run for C
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", partition_key="1"),
        ),
    ),
    AssetDaemonScenario(
        id="test_parent_updated_and_cron",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            partitions_def=daily_partitions_def
        )
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(days=1, hours=7, minutes=1)
        .with_asset_properties(
            keys=["C"],
            # materialize if you haven't been materialized since 7am and your parent is updated and no parents are missing
            auto_materialize_policy=~AutoExecutionPolicy.materialized_since_cron("0 7 * * *")
            & AutoExecutionPolicy.parent_updated()
            & ~AutoExecutionPolicy.parent_missing(),
        ),
        execution_fn=lambda state: state.with_runs(  # both parents update
            run_request(["A", "B"], partition_key=day_partition_key(state.current_time))
        )
        .evaluate_tick()
        # C should be requested
        .assert_requested_runs(
            run_request("C", partition_key=day_partition_key(state.current_time)),
        )
        # on the next day, both parents get materialized
        .with_current_time_advanced(hours=20)
        .with_runs(
            run_request(["A", "B"], partition_key=day_partition_key(state.current_time, delta=1))
        )
        .evaluate_tick()
        # both parents updated, but it's not 7am yet, so C should not be requested
        .assert_requested_runs()
        # now it is after 7am, so C should be requested
        .with_current_time_advanced(hours=4)
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", partition_key=day_partition_key(state.current_time, delta=1)),
        )
        # on the next day, the parents have not been updated yet, so no materialization yet
        .with_current_time_advanced(days=1)
        .evaluate_tick()
        # only A is materialized, so C should not be requested yet
        .with_runs(run_request("A", partition_key=day_partition_key(state.current_time, delta=2)))
        .evaluate_tick()
        # now B is materialized, so C can be requested
        .assert_requested_runs()
        .with_runs(run_request("B", partition_key=day_partition_key(state.current_time, delta=2)))
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", partition_key=day_partition_key(state.current_time, delta=2)),
        ),
    ),
]


@pytest.mark.parametrize("scenario", scenarios, ids=lambda s: s.id)
def test_foo(scenario: AssetDaemonScenario):
    scenario.evaluate_fast()
