import dagster as dg

# One partitioned and one unpartitioned conditioned job side by side: the partitioned
# job launches one run per partition while the unpartitioned job launches a single run.

partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])


@dg.asset(partitions_def=partitions_def)
def part_member() -> None: ...


@dg.asset
def unpart_member() -> None: ...


part_job = dg.define_asset_job(
    "part_job",
    selection=[part_member],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

unpart_job = dg.define_asset_job(
    "unpart_job",
    selection=[unpart_member],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(assets=[part_member, unpart_member], jobs=[part_job, unpart_job])
