from dagster import AutomationCondition, DefaultSensorStatus, Definitions, asset
from dagster._core.definitions.auto_materialize_sensor_definition import (
    UserCodeAutomationConditionSensorDefinition,
)

eager_policy = AutomationCondition.eager().as_auto_materialize_policy()


@asset(auto_materialize_policy=eager_policy)
def upstream() -> None: ...


@asset(
    deps=[upstream],
    auto_materialize_policy=eager_policy,
)
def downstream() -> None: ...


amp_sensor = UserCodeAutomationConditionSensorDefinition(
    "amp_sensor",
    asset_selection="*",
    default_status=DefaultSensorStatus.RUNNING,
)

defs = Definitions(
    assets=[upstream, downstream],
    sensors=[amp_sensor],
)
