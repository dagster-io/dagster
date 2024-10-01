# start_timeout
from dagster import define_asset_job, job


@job(tags={"dagster/max_runtime": 10})
def my_job(): ...


asset_job = define_asset_job(
    name="some_job", selection="*", tags={"dagster/max_runtime": 10}
)
# end_timeout
