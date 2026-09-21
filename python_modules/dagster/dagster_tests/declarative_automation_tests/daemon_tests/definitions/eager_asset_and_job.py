import dagster as dg

# Topology: external -> a -> (b, c)
# "a" has its own eager() automation condition (asset-level).
# "b" and "c" are grouped into a job with all_job_root_assets_match(eager()).
# "external" has no automation condition — it is materialized manually.


@dg.asset
def external() -> None: ...


@dg.asset(deps=[external], automation_condition=dg.AutomationCondition.eager())
def a() -> None: ...


@dg.asset(deps=[a])
def b() -> None: ...


@dg.asset(deps=[a])
def c() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[b, c],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

defs = dg.Definitions(assets=[external, a, b, c], jobs=[my_job])
