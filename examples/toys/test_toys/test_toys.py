from dagster import execute_pipeline
from toys.many_events import define_many_events_pipeline
from toys.resources import define_resource_pipeline


def test_many_events_pipeline():
    assert execute_pipeline(define_many_events_pipeline()).success


def test_resource_pipeline_no_config():
    result = execute_pipeline(define_resource_pipeline())
    assert result.result_for_solid('one').transformed_value() == 2


def test_resource_pipeline_with_config():
    result = execute_pipeline(
        define_resource_pipeline(), environment_dict={'resources': {'R1': {'config': 2}}}
    )
    assert result.result_for_solid('one').transformed_value() == 3
