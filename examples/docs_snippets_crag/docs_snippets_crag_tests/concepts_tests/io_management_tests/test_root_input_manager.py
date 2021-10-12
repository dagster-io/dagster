from dagster import execute_pipeline
from docs_snippets_crag.concepts.io_management.root_input_manager import my_job


def test_execute_pipeline():
    my_job.execute_in_process()
