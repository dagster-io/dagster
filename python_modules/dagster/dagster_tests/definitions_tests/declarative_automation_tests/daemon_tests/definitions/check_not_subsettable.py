import dagster as dg
from dagster._core.definitions.asset_check_spec import AssetCheckSpec

any_dep_newly_updated = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated() | dg.AutomationCondition.will_be_requested()
)


@dg.asset(
    check_specs=[AssetCheckSpec(asset="asset_w_check", name="row_count")],
    automation_condition=dg.AutomationCondition.eager(),
)
def asset_w_check() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


defs = dg.Definitions(assets=[asset_w_check])
