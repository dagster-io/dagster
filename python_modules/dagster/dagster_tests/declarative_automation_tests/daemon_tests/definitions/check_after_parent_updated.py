import dagster as dg

any_dep_newly_updated = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated() | dg.AutomationCondition.will_be_requested()
)


@dg.asset
def raw_files() -> None: ...


@dg.asset(automation_condition=dg.AutomationCondition.eager(), deps=[raw_files])
def processed_files() -> None: ...


@dg.asset_check(asset=processed_files, automation_condition=any_dep_newly_updated)
def row_count() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(assets=[raw_files, processed_files], asset_checks=[row_count])
