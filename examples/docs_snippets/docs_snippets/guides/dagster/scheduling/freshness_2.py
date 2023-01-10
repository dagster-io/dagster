from dagster import (
    AssetSelection,
    Definitions,
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


update_job = define_asset_job(name="update_job", selection=AssetSelection.keys("a"))

# add a reconciliation sensor
update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)

update_job_schedule = ScheduleDefinition(
    name="update_job_schedule", job=update_job, cron_schedule="* * * * *"
)


defs = Definitions(
    assets=[a, b],
    schedules=[update_job_schedule],
    sensors=[update_sensor],
)
