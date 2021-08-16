from dagster import execute_pipeline
from docs_snippets_crag.getting_started.hello_world import hello_graph


def test_hello_graph():
    assert execute_pipeline(hello_graph).success
