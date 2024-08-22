from dagster import AutomationCondition

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    run_request,
)

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import hourly_partitions_def, two_assets_in_sequence


def test_eager_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        two_assets_in_sequence,
        automation_condition=AutomationCondition.eager(),
        ensure_empty_result=False,
    )

    # parent hasn't updated yet
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent updated, now can execute
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # B has not yet materialized, but it has been requested, so don't request again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # same as above
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now B has been materialized, so really shouldn't execute again
    state = state.with_runs(
        *(run_request(ak, pk) for ak, pk in result.true_subset.asset_partitions)
    )
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # A gets materialized again before the hour, execute B again
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1
    # however, B fails
    state = state.with_failed_run_for_asset("B")

    # do not try to materialize B again immediately
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0


def test_eager_hourly_partitioned() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_in_sequence,
            automation_condition=AutomationCondition.eager(),
            ensure_empty_result=False,
        )
        .with_asset_properties(partitions_def=hourly_partitions_def)
        .with_current_time("2020-02-02T01:05:00")
    )

    # parent hasn't updated yet
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # historical parent updated, doesn't matter
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # latest parent updated, now can execute
    state = state.with_runs(run_request("A", "2020-02-02-00:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1
    state = state.with_runs(
        *(run_request(ak, pk) for ak, pk in result.true_subset.asset_partitions)
    )

    # now B has been materialized, so don't execute again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # new partition comes into being, parent hasn't been materialized yet
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent gets materialized, B requested
    state = state.with_runs(run_request("A", "2020-02-02-01:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1
    # but it fails
    state = state.with_failed_run_for_asset("B", "2020-02-02-01:00")

    # B does not get immediately requested again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0
