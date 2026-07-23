import dagster as dg

# A conditioned job whose partitions_def is declared explicitly on the job rather than
# inferred from its member assets. This resolves to the same partitioned JobDefinition
# as the implicit form, so the daemon should treat it identically: one whole-job run
# per requested partition.

partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])


@dg.asset(partitions_def=partitions_def)
def part_asset() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[part_asset],
    partitions_def=partitions_def,
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(assets=[part_asset], jobs=[my_job])
