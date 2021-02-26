from dagster import repository
from docs_snippets.overview.schedules_partitions.partition_definition import date_partition_set
from docs_snippets.overview.schedules_partitions.pipeline import my_data_pipeline


# start_repo_marker_0
@repository
def my_repository():
    return [
        my_data_pipeline,
        date_partition_set,
    ]


# end_repo_marker_0
