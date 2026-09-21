import dagster as dg


@dg.asset
def raw_files() -> None: ...


@dg.asset(automation_condition=dg.AutomationCondition.eager(), deps=[raw_files])
def processed_files() -> None: ...


# Has an automation condition, but a time-gated one that will NOT fire during the test window
# (the cron is far from the frozen test time). DA therefore never individually requests this
# check on the ticks exercised by the test. It is also excluded from the "default" ride-along
# set, because it owns an automation condition.
@dg.asset_check(
    asset=processed_files, automation_condition=dg.AutomationCondition.on_cron("0 0 1 1 *")
)
def yearly_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


# No automation condition -> rides along whenever `processed_files` is materialized.
@dg.asset_check(asset=processed_files)
def non_null() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(assets=[raw_files, processed_files], asset_checks=[yearly_check, non_null])
