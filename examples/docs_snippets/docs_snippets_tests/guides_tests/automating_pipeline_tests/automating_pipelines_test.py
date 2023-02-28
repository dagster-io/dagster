from docs_snippets.guides.dagster.automating_pipelines.airbyte_dbt_sensor import (
    defs as airbtye_dbt_defs,
)


def test_airbyte_sensor():
    assert airbtye_dbt_defs.get_sensor_def("asset_reconciliation_sensor")


from dagster import (
    schedule,
    ScheduleEvaluationContext,
    RunRequest,
    op,
    job,
    build_schedule_context,
    validate_run_config,
)
import datetime
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


from docs_snippets.guides.dagster.automating_pipelines.declare_schedule import (
    defs as declare_schedule_defs,
)
from docs_snippets.guides.dagster.automating_pipelines.declare_schedule import (
    transactions,
    expenses,
    sales,
)
from dagster import materialize


def test_declare_sensor():
    assert declare_schedule_defs.get_sensor_def("update_sensor")


def test_assets():
    result = materialize([transactions, expenses, sales])
    assert result.success
