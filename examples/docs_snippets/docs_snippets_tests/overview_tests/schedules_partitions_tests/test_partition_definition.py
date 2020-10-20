from dagster import execute_pipeline
from docs_snippets.overview.schedules_partitions.partition_definition import day_partition_set
from docs_snippets.overview.schedules_partitions.pipeline import my_pipeline


def test_pipeline():
    result = execute_pipeline(
        my_pipeline, {"solids": {"process_data_for_day": {"config": {"day_of_week": "M"}}}},
    )
    assert result.success


def test_partition_set():
    partitions = day_partition_set.get_partitions()
    assert len(partitions) == 7
    for partition in partitions:
        assert day_partition_set.run_config_for_partition(partition)
