import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset_check(asset=my_asset)
def check_1(): ...


@dg.asset_check(asset=my_asset)
def check_2(): ...


# includes my_asset and both checks
my_job = dg.define_asset_job("my_job", selection=dg.AssetSelection.assets(my_asset))


# includes only my_asset
my_asset_only_job = dg.define_asset_job(
    "my_asset_only_job",
    selection=dg.AssetSelection.assets(my_asset).without_checks(),
)

# includes check_1 and check_2, but not my_asset
checks_only_job = dg.define_asset_job(
    "checks_only_job", selection=dg.AssetSelection.checks_for_assets(my_asset)
)

# includes only check_1
check_1_job = dg.define_asset_job(
    "check_1_job", selection=dg.AssetSelection.checks(check_1)
)

# schedule my_job to run every day at midnight
basic_schedule = dg.ScheduleDefinition(job=my_job, cron_schedule="0 0 * * *")

defs = dg.Definitions(
    assets=[my_asset],
    asset_checks=[check_1, check_2],
    jobs=[my_job, my_asset_only_job, checks_only_job, check_1_job],
    schedules=[basic_schedule],
)
