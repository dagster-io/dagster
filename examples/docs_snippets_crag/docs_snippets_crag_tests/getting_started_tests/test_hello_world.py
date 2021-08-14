from dagster import execute_pipeline
from docs_snippets_crag.getting_started.hello_world import hello_pipeline


def test_hello_pipeline():
    assert execute_pipeline(hello_pipeline).success
