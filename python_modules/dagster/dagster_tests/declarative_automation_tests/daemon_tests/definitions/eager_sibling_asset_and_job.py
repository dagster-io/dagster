import dagster as dg

# An asset-level eager() condition and a conditioned job as SIBLINGS under the same
# root (contrast with eager_asset_and_job, where they are chained and fire across two
# consecutive ticks): one materialization of `external` makes both fire on the SAME
# tick, so a single tick requests an asset materialization AND a whole-job run.
#
#     external            (no condition; materialized manually)
#        |
#        +--> a           asset-level eager()
#        |
#        +--> b, c        my_job: all_job_root_assets_match(eager())


@dg.asset
def external() -> None: ...


@dg.asset(deps=[external], automation_condition=dg.AutomationCondition.eager())
def a() -> None: ...


@dg.asset(deps=[external])
def b() -> None: ...


@dg.asset(deps=[external])
def c() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[b, c],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

defs = dg.Definitions(assets=[external, a, b, c], jobs=[my_job])
