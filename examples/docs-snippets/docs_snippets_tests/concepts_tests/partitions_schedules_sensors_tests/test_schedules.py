from dagster import ScheduleDefinition
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedule_examples import (  # pylint: disable=unused-import
    test_configurable_job_schedule,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    basic_schedule,
    configurable_job_schedule,
    my_timezone_schedule,
)


def test_schedule_definitions():
    for schedule in [basic_schedule, configurable_job_schedule, my_timezone_schedule]:
        assert isinstance(schedule, ScheduleDefinition)
