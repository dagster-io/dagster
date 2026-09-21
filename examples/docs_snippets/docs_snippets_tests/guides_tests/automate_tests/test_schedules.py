from dagster import ScheduleDefinition
from docs_snippets.guides.automate.schedules.basic_asset_schedule import (
    ecommerce_schedule,
)
from docs_snippets.guides.automate.schedules.schedules import (
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
