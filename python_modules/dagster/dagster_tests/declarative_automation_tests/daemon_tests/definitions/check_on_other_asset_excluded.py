import dagster as dg

any_dep_newly_updated = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated() | dg.AutomationCondition.will_be_requested()
)


@dg.asset
def raw_files() -> None: ...


@dg.asset(automation_condition=dg.AutomationCondition.eager(), deps=[raw_files])
def processed_files() -> None: ...


# A conditioned check on `processed_files` -- fires alongside it, so the run takes the DA
# check-resolution path (rather than the no-DA-checks fallback).
@dg.asset_check(asset=processed_files, automation_condition=any_dep_newly_updated)
def row_count() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


# An unconditioned check on `processed_files` -- rides along.
@dg.asset_check(asset=processed_files)
def non_null() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


# A DIFFERENT asset with its own unconditioned check. This check targets `other_asset`, not
# `processed_files`, so it must never be attached to a run that targets `processed_files`.
@dg.asset
def other_asset() -> None: ...


@dg.asset_check(asset=other_asset)
def other_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(
    assets=[raw_files, processed_files, other_asset],
    asset_checks=[row_count, non_null, other_check],
)
