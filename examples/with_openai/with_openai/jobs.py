from dagster import (
    define_asset_job,
)

from .partitions import docs_partitions_def

search_index_job = define_asset_job(
    "search_index_job",
    selection="*search_index",
    partitions_def=docs_partitions_def,
)


question_job = define_asset_job(
    name="question_job",
    selection="completion",
)
