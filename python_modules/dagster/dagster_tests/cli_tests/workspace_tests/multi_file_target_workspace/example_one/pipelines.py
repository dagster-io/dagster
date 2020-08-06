from solids import example_one_solid  # pylint: disable=import-error

from dagster import pipeline


@pipeline
def example_one_pipeline():
    example_one_solid()
