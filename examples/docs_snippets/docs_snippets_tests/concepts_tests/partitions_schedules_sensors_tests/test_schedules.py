import pytest
from dagster import ModeDefinition, build_schedule_context, pipeline, solid, validate_run_config
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedule_examples import (
    my_daily_schedule,
    my_hourly_schedule,
    my_modified_preset_schedule,
    my_monthly_schedule,
    my_preset_schedule,
    my_weekly_schedule,
    test_hourly_schedule,
)


def test_schedule_testing_example():
    test_hourly_schedule()


@pytest.mark.parametrize(
    "schedule_to_test",
    [
        my_hourly_schedule,
        my_daily_schedule,
        my_weekly_schedule,
        my_monthly_schedule,
        my_preset_schedule,
        my_modified_preset_schedule,
    ],
)
def test_schedule_examples(schedule_to_test):
    @solid(config_schema={"date": str})
    def process_data_for_date(_):
        pass

    @pipeline(mode_defs=[ModeDefinition("basic")])
    def pipeline_for_test():
        process_data_for_date()

    schedule_data = schedule_to_test.evaluate_tick(build_schedule_context())

    for run_request in schedule_data.run_requests:
        assert validate_run_config(pipeline_for_test, run_request.run_config)
