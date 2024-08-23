from dagster import AutomationCondition

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import one_asset, one_upstream_observable_asset


def test_newly_updated_condition() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.newly_updated()
    )

    # not updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # still not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated twice in a row
    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_newly_updated_condition_data_version() -> None:
    state = AutomationConditionScenarioState(
        one_upstream_observable_asset,
        automation_condition=AutomationCondition.any_deps_match(
            AutomationCondition.newly_updated()
        ),
    )

    # not updated
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_reported_observation("A", data_version="1")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # same data version, not newly updated
    state = state.with_reported_observation("A", data_version="1")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # new data version
    state = state.with_reported_observation("A", data_version="2")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # new data version
    state = state.with_reported_observation("A", data_version="3")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # no new data version
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0
