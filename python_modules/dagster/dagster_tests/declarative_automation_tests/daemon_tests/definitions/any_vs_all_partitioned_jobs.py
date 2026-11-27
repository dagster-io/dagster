import dagster as dg

partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])


@dg.asset(partitions_def=partitions_def)
def upstream_b() -> None: ...


@dg.asset(partitions_def=partitions_def)
def upstream_c() -> None: ...


@dg.asset(partitions_def=partitions_def, deps=[upstream_b])
def b() -> None: ...


@dg.asset(partitions_def=partitions_def, deps=[upstream_c])
def c() -> None: ...


any_job = dg.define_asset_job(
    "any_job",
    selection=[b, c],
    automation_condition=dg.AutomationCondition.any_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)
all_job = dg.define_asset_job(
    "all_job",
    selection=[b, c],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

defs = dg.Definitions(assets=[upstream_b, upstream_c, b, c], jobs=[any_job, all_job])
