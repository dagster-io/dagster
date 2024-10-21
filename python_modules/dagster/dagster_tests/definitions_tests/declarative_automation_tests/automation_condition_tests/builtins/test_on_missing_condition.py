from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetMaterialization

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    run_request,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    hourly_partitions_def,
    two_assets_in_sequence,
)


def test_on_missing_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        two_assets_in_sequence,
        automation_condition=AutomationCondition.on_missing(),
        ensure_empty_result=False,
    )

    # B starts off as materialized
    state.instance.report_runless_asset_event(AssetMaterialization(asset_key=AssetKey("B")))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent materialized, now could execute, but B is not missing
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now wipe B so that it is newly missing, should update
    state.instance.wipe_assets([AssetKey("B")])
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # B has not yet materialized, but it has been requested, so don't request again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # same as above
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent materialized again, no impact
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now B has been materialized, so really shouldn't execute again
    state = state.with_runs(
        *(
            run_request(ak, pk)
            for ak, pk in result.true_subset.expensively_compute_asset_partitions()
        )
    )
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent materialized again, no impact
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0


def test_on_missing_hourly_partitioned() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_in_sequence,
            automation_condition=AutomationCondition.on_missing(),
            ensure_empty_result=False,
        )
        .with_asset_properties(partitions_def=hourly_partitions_def)
        .with_current_time("2020-02-02T00:05:00")
    )

    # parent hasn't updated yet
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    state = state.with_current_time_advanced(hours=1)

    # historical parent updated, doesn't matter
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # latest parent updated, now can execute
    state = state.with_runs(run_request("A", "2020-02-02-00:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # B has been requested, so don't request again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # new partition comes into being, parent hasn't been materialized yet
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # latest parent updated, now can execute
    state = state.with_runs(run_request("A", "2020-02-02-01:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # latest parent updated again, don't re execute
    state = state.with_runs(run_request("A", "2020-02-02-01:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0


def test_on_missing_without_time_limit() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_in_sequence,
            automation_condition=AutomationCondition.on_missing().without(
                AutomationCondition.in_latest_time_window()
            ),
            ensure_empty_result=False,
        )
        .with_asset_properties(partitions_def=hourly_partitions_def)
        .with_current_time("2019-02-02T01:05:00")
    )

    # parent hasn't updated yet
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    state = state.with_current_time_advanced(years=1)

    # historical parents updated, matters
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    state = state.with_runs(run_request("A", "2019-04-05-00:00"))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 2

    # B has been requested, so don't request again
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0
