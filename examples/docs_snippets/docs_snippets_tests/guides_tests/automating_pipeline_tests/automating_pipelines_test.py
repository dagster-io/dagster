import datetime

from dagster import (
    build_schedule_context,
    materialize,
    validate_run_config,
)
from docs_snippets.guides.dagster.automating_pipelines.config_schedule import (
    configurable_job,
)
from docs_snippets.guides.dagster.automating_pipelines.declare_schedule import (
    finance_report,
    sales_report,
    transactions_cleaned,
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


def test_assets():
    result = materialize([transactions_cleaned, sales_report, finance_report])
    assert result.success
