from typing import Optional

import pytest
from dagster import AutoMaterializePolicy, SchedulingCondition

from ..scenario_specs import diamond
from .asset_condition_scenario import AssetConditionScenarioState


@pytest.mark.parametrize(
    "b_condition, c_condition, d_condition, expected_child_descriptions",
    [
        (None, None, None, []),
        (None, None, SchedulingCondition.missing(), []),
        (None, SchedulingCondition.missing(), None, ["Condition of C"]),
        (
            SchedulingCondition.missing(),
            SchedulingCondition.missing(),
            None,
            ["Condition of B, C"],
        ),
        (
            SchedulingCondition.eager(),
            SchedulingCondition.eager(),
            None,
            ["Condition of B, C"],
        ),
        (
            SchedulingCondition.eager(),
            SchedulingCondition.missing(),
            None,
            ["Condition of B", "Condition of C"],
        ),
        # recursive child condition
        (
            SchedulingCondition.child_condition(),
            SchedulingCondition.child_condition(),
            SchedulingCondition.missing(),
            ["Condition of D"],
        ),
        (
            SchedulingCondition.child_condition(),
            SchedulingCondition.child_condition(),
            None,
            [],
        ),
        (
            SchedulingCondition.child_condition(),
            SchedulingCondition.missing(),
            SchedulingCondition.missing(),
            ["Condition of C, D"],
        ),
        (
            SchedulingCondition.child_condition(),
            SchedulingCondition.missing(),
            SchedulingCondition.eager(),
            ["Condition of C", "Condition of D"],
        ),
    ],
)
def test_child_condition(
    b_condition: Optional[SchedulingCondition],
    c_condition: Optional[SchedulingCondition],
    d_condition: Optional[SchedulingCondition],
    expected_child_descriptions,
) -> None:
    b_policy, c_policy, d_policy = (
        AutoMaterializePolicy.from_asset_condition(c) if c else None
        for c in [b_condition, c_condition, d_condition]
    )

    state = (
        AssetConditionScenarioState(
            diamond,
            asset_condition=SchedulingCondition.child_condition(),
            ensure_empty_result=False,
        )
        .with_asset_properties("B", auto_materialize_policy=b_policy)
        .with_asset_properties("C", auto_materialize_policy=c_policy)
        .with_asset_properties("D", auto_materialize_policy=d_policy)
    )

    state, result = state.evaluate("A")
    child_results = result.child_results
    if len(expected_child_descriptions) > 1:
        # If there are multiple children, the child results are nested under an OR
        assert len(child_results) == 1
        or_result = next(iter(child_results))
        assert or_result.condition.description == "Any of"
        child_results = or_result.child_results
    assert len(child_results) == len(expected_child_descriptions)
    for child_result, expected_description in zip(child_results, expected_child_descriptions):
        assert expected_description in child_result.condition.description
