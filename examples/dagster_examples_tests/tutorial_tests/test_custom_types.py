from dagster_examples.intro_tutorial.custom_types import burger_time

from dagster import execute_pipeline_with_preset


def test_custom_types_example():
    assert execute_pipeline_with_preset(burger_time, 'test_input').success
    assert execute_pipeline_with_preset(burger_time, 'test_output').success
