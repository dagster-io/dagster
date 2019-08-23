from dagster_examples.intro_tutorial.custom_types import burger_time

from dagster import execute_pipeline


def test_custom_types_example():
    assert execute_pipeline(**burger_time.get_preset('test')).success
