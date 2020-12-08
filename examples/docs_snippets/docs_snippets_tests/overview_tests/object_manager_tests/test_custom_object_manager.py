from dagster import execute_pipeline
from docs_snippets.overview.object_managers.custom_object_manager import my_pipeline


def test_custom_object_manager():
    execute_pipeline(my_pipeline)
