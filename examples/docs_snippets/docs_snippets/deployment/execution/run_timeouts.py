# start_timeout
import dagster as dg


@dg.job(tags={"dagster/max_runtime": 10})
def my_job(): ...


asset_job = dg.define_asset_job(
    name="some_job", selection="*", tags={"dagster/max_runtime": 10}
)
# end_timeout
