import datetime

from dagster import build_schedule_context, validate_run_config
from docs_snippets.guides.dagster.automating_pipelines.config_schedule import (
    configurable_job,
)


def test_configurable_job_schedule():
    context = build_schedule_context(
        scheduled_execution_time=datetime.datetime(2023, 1, 1)
    )
    if context.scheduled_execution_time.weekday() < 5:
        activity_selection = "grind"
    else:
        activity_selection = "party"
    assert validate_run_config(
        configurable_job,
        run_config={
            "ops": {
                "configurable_op": {
                    "config": {"activity_selection": activity_selection}
                }
            }
        },
    )
