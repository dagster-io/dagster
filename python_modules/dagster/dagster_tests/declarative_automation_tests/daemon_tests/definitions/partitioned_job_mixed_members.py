import dagster as dg

# A conditioned partitioned job containing an unpartitioned member asset and an asset
# check: each partition run also re-materializes the unpartitioned member (with no
# partition) and executes the check.

partitions_def = dg.StaticPartitionsDefinition(["p1", "p2"])


@dg.asset(partitions_def=partitions_def)
def part_asset() -> None: ...


@dg.asset
def unpart_asset() -> None: ...


@dg.asset_check(asset=unpart_asset)
def unpart_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=part_asset)
def part_asset_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


my_job = dg.define_asset_job(
    "my_job",
    selection=[part_asset, unpart_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(
    assets=[part_asset, unpart_asset],
    asset_checks=[unpart_check, part_asset_check],
    jobs=[my_job],
)
