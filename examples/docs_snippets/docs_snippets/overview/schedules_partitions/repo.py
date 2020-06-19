from docs_snippets.overview.schedules_partitions.partition_definition import day_partition_set
from docs_snippets.overview.schedules_partitions.pipeline import my_pipeline

from dagster import repository


@repository
def my_repository():
    return [
        my_pipeline,
        day_partition_set,
    ]
