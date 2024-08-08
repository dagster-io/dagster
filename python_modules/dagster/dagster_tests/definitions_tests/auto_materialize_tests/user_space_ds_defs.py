from dagster import (
    AutomationCondition,
    AutomationConditionSensorDefinition,
    DefaultSensorStatus,
    Definitions,
    asset,
)

eager_policy = AutomationCondition.eager().as_auto_materialize_policy()


@asset(auto_materialize_policy=eager_policy)
def upstream() -> None: ...


@asset(
    deps=[upstream],
    auto_materialize_policy=eager_policy,
)
def downstream() -> None: ...


amp_sensor = AutomationConditionSensorDefinition(
    "amp_sensor",
    asset_selection="*",
    default_status=DefaultSensorStatus.RUNNING,
    user_code=True,
)

defs = Definitions(
    assets=[upstream, downstream],
    sensors=[amp_sensor],
)
