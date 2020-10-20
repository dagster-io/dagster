from dagster import pipeline
from solids import example_two_solid  # pylint: disable=import-error


@pipeline
def example_two_pipeline():
    example_two_solid()
