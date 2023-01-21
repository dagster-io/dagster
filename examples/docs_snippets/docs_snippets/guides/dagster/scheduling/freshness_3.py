from dagster import (
    AssetSelection,
    Definitions,
    FreshnessPolicy,
    ScheduleDefinition,
    asset,
    build_asset_reconciliation_sensor,
    define_asset_job,
)


@asset
def a():
    pass


@asset
def b(a):
    pass


# add a freshness policy
@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=2))
def c(a):
    pass


update_job = define_asset_job(name="update_job", selection=AssetSelection.keys("a"))

update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)

update_job_schedule = ScheduleDefinition(
    name="update_job_schedule", job=update_job, cron_schedule="* * * * *"
)

defs = Definitions(
    assets=[a, b, c],
    schedules=[update_job_schedule],
    sensors=[update_sensor],
)
