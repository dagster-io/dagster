from dagster import execute_pipeline
from docs_snippets_crag.concepts.io_management.root_input_manager import my_pipeline


def test_execute_pipeline():
    execute_pipeline(my_pipeline)
