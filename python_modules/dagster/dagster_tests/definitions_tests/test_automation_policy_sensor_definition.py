import pytest
from dagster import AssetSelection, DefaultSensorStatus, build_sensor_context
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)


@pytest.mark.parametrize(
    "selection", [AssetSelection.all(), AssetSelection.assets("asset1", "asset2")]
)
def test_constructor(selection):
    tags = {"apple": "banana", "orange": "kiwi"}
    automation_sensor = AutomationConditionSensorDefinition(
        "foo",
        asset_selection=selection,
        run_tags=tags,
        description="fdsjkl",
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=50,
    )
    assert automation_sensor.name == "foo"
    assert automation_sensor.run_tags == tags
    assert automation_sensor.asset_selection == selection
    assert automation_sensor.description == "fdsjkl"
    assert automation_sensor.default_status == DefaultSensorStatus.RUNNING
    assert automation_sensor.minimum_interval_seconds == 50

    with pytest.raises(
        NotImplementedError,
        match="Automation policy sensors cannot be evaluated like regular user-space sensors.",
    ):
        automation_sensor(build_sensor_context())
