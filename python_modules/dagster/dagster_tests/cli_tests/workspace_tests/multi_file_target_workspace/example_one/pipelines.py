# type: ignore
from dagster._legacy import pipeline
from solids import example_one_solid


@pipeline
def example_one_pipeline():
    example_one_solid()
