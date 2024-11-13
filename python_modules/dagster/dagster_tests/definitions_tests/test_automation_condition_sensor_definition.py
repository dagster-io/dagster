import pytest
from dagster import AssetSelection, DefaultSensorStatus, build_sensor_context
from dagster._check.functions import ParameterCheckError
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.instance import DagsterInstance
from dagster_test.toys.auto_materializing.large_graph import AssetLayerConfig, build_assets


@pytest.mark.parametrize(
    "selection", [AssetSelection.all(), AssetSelection.assets("asset1", "asset2")]
)
@pytest.mark.parametrize("user_code", [True, False])
def test_constructor(selection: AssetSelection, user_code: bool) -> None:
    tags = {"apple": "banana", "orange": "kiwi"}
    automation_sensor = AutomationConditionSensorDefinition(
        "foo",
        target=selection,
        run_tags=tags,
        description="fdsjkl",
        default_status=DefaultSensorStatus.RUNNING,
        minimum_interval_seconds=50,
        use_user_code_server=user_code,
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
            "foo", target="*", default_condition=AutomationCondition.eager()
        )

    sensor = AutomationConditionSensorDefinition(
        "foo",
        target="*",
        default_condition=AutomationCondition.eager(),
        use_user_code_server=True,
    )
    assert sensor.default_condition == AutomationCondition.eager()


def test_limits() -> None:
    sensor = AutomationConditionSensorDefinition("foo", target="*", use_user_code_server=True)

    defs = Definitions(
        assets=build_assets(
            "test",
            layer_configs=[AssetLayerConfig(1000)],
            automation_condition=AutomationCondition.eager(),
        )
    )
    with pytest.raises(DagsterInvalidInvocationError, match='"foo" targets 1000 assets or checks'):
        sensor(
            build_sensor_context(
                instance=DagsterInstance.ephemeral(),
                repository_def=defs.get_repository_def(),
            ),
        )

    # more than 500 total assets, but only 400 with a condition
    with_condition = build_assets(
        "cond",
        layer_configs=[AssetLayerConfig(400)],
        automation_condition=AutomationCondition.eager(),
    )
    without_condition = build_assets(
        "no_cond",
        layer_configs=[AssetLayerConfig(400)],
        automation_condition=None,
    )
    defs = Definitions(assets=[*with_condition, *without_condition])
    sensor(
        build_sensor_context(
            instance=DagsterInstance.ephemeral(),
            repository_def=defs.get_repository_def(),
        ),
    )
