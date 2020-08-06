from solids import example_two_solid  # pylint: disable=import-error

from dagster import pipeline


@pipeline
def example_two_pipeline():
    example_two_solid()
