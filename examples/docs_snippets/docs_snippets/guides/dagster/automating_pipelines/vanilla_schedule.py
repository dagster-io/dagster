# ruff: isort: skip_file

from dagster import asset

# vanilla_schedule_start

from dagster import AssetSelection, define_asset_job, ScheduleDefinition

asset_job = define_asset_job("asset_job", AssetSelection.groups("some_asset_group"))

basic_schedule = ScheduleDefinition(job=asset_job, cron_schedule="0 9 * * *")

# vanilla_schedule_end
