from dagster import ScheduleDefinition
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    my_timezone_schedule,
    configurable_job_schedule,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.basic_asset_schedule import (
    ecommerce_schedule,
)


def test_schedule_definitions():
    for schedule in [
        configurable_job_schedule,
        ecommerce_schedule,
        my_timezone_schedule,
    ]:
        assert isinstance(schedule, ScheduleDefinition)
