import dagster as dg

static_partitions1 = dg.StaticPartitionsDefinition(["x", "y", "z"])
static_partitions2 = dg.StaticPartitionsDefinition(["t", "u", "v"])

condition = dg.AutomationCondition.missing() & ~dg.AutomationCondition.in_progress()


@dg.asset(
    automation_condition=condition,
)
def A() -> None: ...


@dg.asset(
    deps=[A],
    automation_condition=condition,
    partitions_def=static_partitions2,
)
def B() -> None: ...


@dg.asset(
    deps=[A],
    automation_condition=condition,
    partitions_def=static_partitions1,
)
def C() -> None: ...


@dg.asset(
    deps=[C],
    automation_condition=condition,
    partitions_def=static_partitions1,
)
def D() -> None: ...


@dg.asset(
    deps=[D],
    automation_condition=condition,
)
def E() -> None: ...


defs = dg.Definitions(
    assets=[A, B, C, D, E],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            "the_sensor", asset_selection="*", use_user_code_server=True
        )
    ],
)
