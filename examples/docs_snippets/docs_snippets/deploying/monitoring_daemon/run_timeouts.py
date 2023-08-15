# start_timeout
from dagster import MAX_RUNTIME_SECONDS_TAG, define_asset_job, job


@job(tags={MAX_RUNTIME_SECONDS_TAG: 10})
def my_job():
    ...


asset_job = define_asset_job(
    name="some_job", selection="*", tags={MAX_RUNTIME_SECONDS_TAG: 10}
)
# end_timeout
