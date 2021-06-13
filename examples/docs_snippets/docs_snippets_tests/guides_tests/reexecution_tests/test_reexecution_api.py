from dagster import execute_pipeline
from docs_snippets.guides.dagster.reexecution.reexecution_api import reexecution


def test_reexecution_api():
    reexecution()
