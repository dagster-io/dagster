from typing import Sequence

from dagster import (
    AssetKey,
    AutomationCondition,
    DagsterInstance,
    asset,
    evaluate_automation_conditions,
)
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition,
)


def _get_result(key: CoercibleToAssetKey, results: Sequence[AutomationResult]) -> AutomationResult:
    key = AssetKey.from_coercible(key)
    for result in results:
        if result.asset_key == key:
            return result
    assert False


def test_basic() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    cond2 = AutomationCondition.eager()

    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    @asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def b(): ...

    result = evaluate_automation_conditions([a, b], instance=DagsterInstance.ephemeral())

    a_result = _get_result(a.key, result.results)
    assert len(a_result.child_results) == 1
    assert a_result.child_results[0].child_results[0].condition == cond2


def test_multiple_downstreams() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    cond2 = AutomationCondition.in_progress()
    cond3 = AutomationCondition.missing()

    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    # Left hand side, chain of lazy into two different policies
    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[a])
    def left1(): ...

    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[left1])
    def left2(): ...

    @asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[left2])
    def b(): ...

    @asset(auto_materialize_policy=cond3.as_auto_materialize_policy(), deps=[left2])
    def c(): ...

    # Right hand side, same policy as b
    @asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def d(): ...

    result = evaluate_automation_conditions(
        [a, left1, left2, b, c, d], instance=DagsterInstance.ephemeral()
    )

    # make sure a has all downstreams
    a_result = _get_result(a.key, result.results)
    assert len(a_result.child_results) == 2

    res1 = a_result.child_results[0]
    assert res1.condition.description == "b,d"
    assert res1.child_results[0].condition == cond2

    res2 = a_result.child_results[1]
    assert res2.condition.description == "c"
    assert res2.child_results[0].condition == cond3


def test_multiple_downstreams_nested() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    # combine the lazy condition with another condition, ensure we don't infinite loop
    cond2 = AutomationCondition.any_downstream_conditions() & ~AutomationCondition.in_progress()
    cond3 = AutomationCondition.eager()

    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    @asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def b(): ...

    @asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[b])
    def c(): ...

    # Right hand side, same policy as b
    @asset(auto_materialize_policy=cond3.as_auto_materialize_policy(), deps=[c])
    def d(): ...

    result = evaluate_automation_conditions([a, b, c, d], instance=DagsterInstance.ephemeral())

    # make sure a has all downstreams
    a_result = _get_result(a.key, result.results)
    assert len(a_result.child_results) == 2

    # the first condition is a bit gnarly, but it should resolve to b: ((d: eager) & ~in_progress)
    res1 = a_result.child_results[0]
    assert res1.condition.description == "b"
    res1_and = res1.child_results[0]
    assert isinstance(res1_and.condition, AndAutomationCondition)
    res1_1 = res1_and.child_results[0].child_results[0]
    assert res1_1.condition.description == "d"
    assert res1_1.child_results[0].condition == cond3
    res1_2 = res1_and.child_results[1]
    assert res1_2.condition == ~AutomationCondition.in_progress()

    # the second condition resolves to just (d: eager)
    res2 = a_result.child_results[1]
    assert res2.condition.description == "d"
    assert res2.child_results[0].condition == cond3
