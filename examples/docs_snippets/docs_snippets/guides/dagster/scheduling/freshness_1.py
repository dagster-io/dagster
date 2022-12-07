from dagster import (
    AssetSelection,
    ScheduleDefinition,
    asset,
    define_asset_job,
    repository,
)


@asset
def a():
    pass


@asset
def b(a):
    pass


update_job = define_asset_job(
    name="update_job", selection=AssetSelection.keys("a", "b")
)

update_job_schedule = ScheduleDefinition(
    name="update_job_schedule", job=update_job, cron_schedule="* * * * *"
)


@repository
def my_repo():
    return [[a, b], [update_job_schedule]]
