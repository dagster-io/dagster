from dagster import execute_pipeline
from docs_snippets.overview.schedules_partitions.partition_definition import date_partition_set
from docs_snippets.overview.schedules_partitions.pipeline import my_data_pipeline


def test_pipeline():
    result = execute_pipeline(
        my_data_pipeline,
        {"solids": {"process_data_for_date": {"config": {"date": "2018-05-01"}}}},
    )
    assert result.success


def test_partition_set():
    partitions = date_partition_set.get_partitions()
    assert len(partitions) == 31
    for partition in partitions:
        assert date_partition_set.run_config_for_partition(partition)
