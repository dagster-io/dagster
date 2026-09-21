import dagster as dg

# A job over a never-materialized asset with all_job_root_assets_match(missing()) fires on the
# very first tick, so a single tick exercises the job-entity run submission path (and, with
# a crash flag, its interrupted-tick retry).


@dg.asset
def only_asset() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[only_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(assets=[only_asset], jobs=[my_job])
