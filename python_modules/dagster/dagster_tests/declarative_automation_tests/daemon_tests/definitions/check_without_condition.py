import dagster as dg


@dg.asset
def raw_files() -> None: ...


@dg.asset(automation_condition=dg.AutomationCondition.eager(), deps=[raw_files])
def processed_files() -> None: ...


# These checks have NO automation condition of their own. They are not individually
# requested by the automation tick -- they ride along with any run that materializes
# `processed_files`. The run request should therefore record all of them explicitly.
@dg.asset_check(asset=processed_files)
def row_count() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=processed_files)
def non_null() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(assets=[raw_files, processed_files], asset_checks=[row_count, non_null])
