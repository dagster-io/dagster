# type: ignore

from dagster._legacy import pipeline
from solids import example_two_solid


@pipeline
def example_two_pipeline():
    example_two_solid()
