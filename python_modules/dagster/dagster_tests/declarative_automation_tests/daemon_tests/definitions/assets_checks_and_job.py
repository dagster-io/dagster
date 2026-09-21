import dagster as dg

# Assets, an asset check, and a job all carrying automation conditions, with no explicit
# sensor: the default automation condition sensor evaluates all three entity types.

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


# the job covers a separate asset so its run is distinguishable from the asset/check runs
@dg.asset
def job_member() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[job_member],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(
    assets=[raw_files, processed_files, job_member],
    asset_checks=[row_count],
    jobs=[my_job],
)
