# ruff: isort: skip_file

# start_asset_marker

from dagster import asset


@asset
def hello():
    return "hello"


@asset(deps=[hello])
def world():
    return "world"


# end_asset_marker


# start_job_marker

from dagster import define_asset_job

hello_world_job = define_asset_job("hello_world_job", selection="hello+")

# end_job_marker


# start_schedule_marker
from dagster import ScheduleDefinition

hello_schedule = ScheduleDefinition(
    name="my_first_schedule",
    cron_schedule="0 4 * * *",
    job=hello_world_job,
    description="A daily schedule that says hello and world",
)

# end_schedule_marker

# start_pipeline_marker

from dagster import Definitions

defs = Definitions(
    assets=[hello, world],
    jobs=[hello_world_job],
    schedules=[hello_schedule],
)

# end_pipeline_marker
