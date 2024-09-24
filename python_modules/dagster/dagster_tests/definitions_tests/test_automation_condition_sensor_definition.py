import pytest
from dagster import AssetSelection, DefaultSensorStatus, build_sensor_context
from dagster._check.functions import ParameterCheckError
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)


@pytest.mark.parametrize(
    "selection", [AssetSelection.all(), AssetSelection.assets("asset1", "asset2")]
)
@pytest.mark.parametrize("user_code", [True, False])
def test_constructor(selection: AssetSelection, user_code: bool) -> None:
    tags = {"apple": "banana", "orange": "kiwi"}
    automation_sensor = AutomationConditionSensorDefinition(
        "foo",
        asset_selection=selection,
        run_tags=tags,
        description="fdsjkl",
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=50,
        user_code=user_code,
    )
    assert automation_sensor.name == "foo"
    assert automation_sensor.run_tags == tags
    assert automation_sensor.asset_selection == selection
    assert automation_sensor.description == "fdsjkl"
    assert automation_sensor.default_status == DefaultSensorStatus.RUNNING
    assert automation_sensor.minimum_interval_seconds == 50

    if not user_code:
        with pytest.raises(
            NotImplementedError,
            match="Automation condition sensors cannot be evaluated like regular user-space sensors.",
        ):
            automation_sensor(build_sensor_context())


def test_default_condition() -> None:
    with pytest.raises(ParameterCheckError, match="non-user-code"):
        AutomationConditionSensorDefinition(
            "foo", asset_selection="*", default_condition=AutomationCondition.eager()
        )

    sensor = AutomationConditionSensorDefinition(
        "foo", asset_selection="*", default_condition=AutomationCondition.eager(), user_code=True
    )
    assert sensor.default_condition == AutomationCondition.eager()
