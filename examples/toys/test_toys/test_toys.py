from dagster import execute_pipeline
from toys.many_events import define_many_events_pipeline


def test_many_events_pipeline():
    assert execute_pipeline(define_many_events_pipeline()).success
