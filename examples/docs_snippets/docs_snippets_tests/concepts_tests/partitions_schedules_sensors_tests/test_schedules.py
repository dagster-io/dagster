from dagster import ScheduleDefinition
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    configurable_job_schedule,
    ecommerce_schedule,
    my_timezone_schedule,
)


def test_schedule_definitions():
    for schedule in [
        configurable_job_schedule,
        ecommerce_schedule,
        my_timezone_schedule,
    ]:
        assert isinstance(schedule, ScheduleDefinition)
