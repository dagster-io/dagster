from dagster import execute_pipeline
from docs_snippets_crag.concepts.io_management.custom_io_manager import (  # pylint: disable=E0401
    my_pipeline,
    my_pipeline_with_metadata,
)


def test_custom_io_manager():
    execute_pipeline(my_pipeline)


def test_custom_io_manager_with_metadata():
    execute_pipeline(my_pipeline_with_metadata)
