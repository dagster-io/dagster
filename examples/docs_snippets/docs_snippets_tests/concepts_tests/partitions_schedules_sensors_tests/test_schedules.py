from datetime import datetime
from typing import cast

from dagster import (
    Definitions,
    RunRequest,
    ScheduleDefinition,
    build_schedule_context,
    validate_run_config,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.basic_asset_schedule import (
    ecommerce_schedule,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    configurable_asset,
    configurable_job,
    configurable_job_schedule,
    my_timezone_schedule,
)


def test_schedule_definitions():
    for schedule in [
        configurable_job_schedule,
        ecommerce_schedule,
        my_timezone_schedule,
    ]:
        assert isinstance(schedule, ScheduleDefinition)


def test_configurable_job_schedule():
    run_request = cast(
        RunRequest,
        configurable_job_schedule(
            build_schedule_context(scheduled_execution_time=datetime(2020, 1, 1))
        ),
    )
    assert run_request.tags == {"date": "2020-01-01"}

    defs = Definitions(assets=[configurable_asset], jobs=[configurable_job])
    assert validate_run_config(
        defs.get_job_def("configurable_job"), run_request.run_config
    )
