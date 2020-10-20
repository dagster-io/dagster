from dagster import pipeline
from solids import example_one_solid  # pylint: disable=import-error


@pipeline
def example_one_pipeline():
    example_one_solid()
