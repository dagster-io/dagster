from dagster import ScheduleDefinition
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    ecommerce_schedule,
    configurable_job_schedule,
    my_timezone_schedule,
)


def test_schedule_definitions():
    for schedule in [
        ecommerce_schedule,
        configurable_job_schedule,
        my_timezone_schedule,
    ]:
        assert isinstance(schedule, ScheduleDefinition)
