from dagster import execute_pipeline
from docs_snippets.concepts.io_management.custom_io_manager import my_pipeline


def test_custom_io_manager():
    execute_pipeline(my_pipeline)
