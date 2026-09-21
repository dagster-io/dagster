import dagster as dg

# A conditioned job over a partitioned asset: each partition evaluates independently,
# and each requested partition becomes its own whole-job run.

partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])


@dg.asset(partitions_def=partitions_def)
def part_asset() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[part_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(assets=[part_asset], jobs=[my_job])
