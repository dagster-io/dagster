import dagster as dg

static_partitions1 = dg.StaticPartitionsDefinition(["x", "y", "z"])
static_partitions2 = dg.StaticPartitionsDefinition(["t", "u", "v"])

condition = dg.AutomationCondition.missing() & ~dg.AutomationCondition.in_progress()


@dg.asset(
    automation_condition=condition,
    check_specs=[dg.AssetCheckSpec(name="inside", asset="backfillA")],
)
def backfillA() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


@dg.asset(
    deps=[backfillA],
    automation_condition=condition,
    partitions_def=static_partitions2,
    check_specs=[dg.AssetCheckSpec(name="inside", asset="backfillB")],
)
def backfillB() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


@dg.asset(
    deps=[backfillA],
    automation_condition=condition,
    partitions_def=static_partitions1,
)
def backfillC() -> None: ...


@dg.asset(
    automation_condition=condition,
    check_specs=[dg.AssetCheckSpec(name="inside", asset="run1")],
)
def run1() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


@dg.asset(
    automation_condition=condition,
    partitions_def=static_partitions1,
    check_specs=[dg.AssetCheckSpec(name="inside", asset="run2")],
)
def run2() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


# these checks should never be executed as they are not required
# and do not have an automation condition
@dg.asset_check(name="outside", asset="backfillA")
def outsideA() -> dg.AssetCheckResult: ...


@dg.asset_check(name="outside", asset="backfillB")
def outsideB() -> dg.AssetCheckResult: ...


@dg.asset_check(name="outside", asset="run1")
def outside1() -> dg.AssetCheckResult: ...


@dg.asset_check(name="outside", asset="run2")
def outside2() -> dg.AssetCheckResult: ...


defs = dg.Definitions(
    assets=[backfillA, backfillB, backfillC, run1, run2],
    asset_checks=[outsideA, outsideB, outside1, outside2],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            "the_sensor", asset_selection="*", use_user_code_server=True
        )
    ],
)
