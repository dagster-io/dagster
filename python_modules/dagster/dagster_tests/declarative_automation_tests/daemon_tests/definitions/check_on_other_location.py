import dagster as dg

any_dep_newly_updated = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated() | dg.AutomationCondition.will_be_requested()
)


# processed_files exists in `check_after_parent_updated.py`
@dg.asset_check(asset=dg.AssetKey("processed_files"), automation_condition=any_dep_newly_updated)
def no_nulls() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(asset_checks=[no_nulls])
