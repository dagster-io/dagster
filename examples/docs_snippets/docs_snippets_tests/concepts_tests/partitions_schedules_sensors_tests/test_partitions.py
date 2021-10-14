import pytest
from dagster import build_schedule_context, execute_pipeline, validate_run_config
from docs_snippets.concepts.partitions_schedules_sensors.partition_definition import (
    date_partition_set,
    my_schedule,
    test_my_partition_set,
    weekday_partition_set,
)
from docs_snippets.concepts.partitions_schedules_sensors.pipeline import my_data_pipeline


def test_pipeline():
    result = execute_pipeline(
        my_data_pipeline,
        {"solids": {"process_data_for_date": {"config": {"date": "2018-05-01"}}}},
    )
    assert result.success


@pytest.mark.parametrize("partition_set", [date_partition_set, weekday_partition_set])
def test_pipeline_with_partition_set(partition_set):
    for partition in partition_set.get_partitions():
        run_config = partition_set.run_config_for_partition(partition)
        result = execute_pipeline(
            my_data_pipeline,
            run_config=run_config,
        )
        assert result.success


def test_partition_set_test_example():
    test_my_partition_set()


def test_partition_schedule():
    schedule_data = my_schedule.evaluate_tick(build_schedule_context())
    for run_request in schedule_data.run_requests:
        validate_run_config(my_data_pipeline, run_request.run_config)
