# ruff: isort: skip_file
import datetime

from .schedules import configurable_job_schedule, configurable_job


# start_test_cron_schedule_context
import dagster as dg


def test_configurable_job_schedule():
    with dg.build_schedule_context(
        scheduled_execution_time=datetime.datetime(2020, 1, 1)
    ) as context:
        run_request = dg.configurable_job_schedule(context)
        assert dg.validate_run_config(configurable_job, run_request.run_config)


# end_test_cron_schedule_context
