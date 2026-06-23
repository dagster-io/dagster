import dagster as dg


def load_sales_data() -> int:
    return 1500


@dg.asset
def daily_sales() -> dg.MaterializeResult:
    row_count = load_sales_data()
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset_check(asset="daily_sales")
def sales_row_count_check(
    context: dg.AssetCheckExecutionContext,
) -> dg.AssetCheckResult:
    event = context.instance.get_latest_materialization_event(
        dg.AssetKey("daily_sales")
    )
    metadata = event.asset_materialization.metadata
    row_count = metadata["row_count"].value
    passed = row_count > 1000
    return dg.AssetCheckResult(
        passed=passed,
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={"row_count": row_count},
    )


all_deps_checks_passed = dg.AutomationCondition.all_deps_match(
    dg.AutomationCondition.all_checks_match(
        ~dg.AutomationCondition.check_failed()
        | dg.AutomationCondition.will_be_requested(),
    )
)


@dg.asset(
    deps=["daily_sales"],
    automation_condition=dg.AutomationCondition.eager() & all_deps_checks_passed,
)
def analytics(): ...
