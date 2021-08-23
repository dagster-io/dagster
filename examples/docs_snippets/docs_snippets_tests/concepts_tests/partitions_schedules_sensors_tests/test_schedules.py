from datetime import datetime

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
    test_my_cron_schedule,
    test_my_cron_schedule_with_context,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    my_daily_schedule as partition_schedule_example,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    my_execution_time_schedule,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    my_schedule as non_partition_schedule_example,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedules.schedules import (
    my_timezone_schedule,
)


def test_partition_based_schedule_example():
    @solid(config_schema={"date": str})
    def process_data_for_date(context):
        return context.solid_config["date"]

    @pipeline
    def pipeline_for_test():
        process_data_for_date()

    run_config = partition_schedule_example(datetime(2021, 1, 1))

    assert validate_run_config(pipeline_for_test, run_config)

    run_config = my_timezone_schedule(datetime(2021, 1, 1))

    assert validate_run_config(pipeline_for_test, run_config)


def test_non_partition_schedule_example():
    @solid(config_schema={"dataset_name": str})
    def process_data(_):
        pass

    @pipeline
    def pipeline_for_test():
        process_data()

    run_config = non_partition_schedule_example()
    assert validate_run_config(pipeline_for_test, run_config)


def test_my_execution_time_schedule():
    @solid(config_schema={"dataset_name": str, "execution_date": str})
    def process_data(_):
        pass

    @pipeline
    def pipeline_for_test():
        process_data()

    run_config = my_execution_time_schedule(
        build_schedule_context(scheduled_execution_time=datetime(2021, 1, 1))
    )
    assert validate_run_config(pipeline_for_test, run_config)


def test_schedule_testing_examples():
    test_hourly_schedule()
    test_my_cron_schedule()
    test_my_cron_schedule_with_context()


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

    run_config = schedule_to_test(datetime(2021, 1, 1))

    assert validate_run_config(pipeline_for_test, run_config)
