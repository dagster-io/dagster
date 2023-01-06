# mypy: disable-error-code=attr-defined
from dagster._legacy import pipeline
from solids import example_two_solid  # pylint: disable=no-name-in-module


@pipeline
def example_two_pipeline():
    example_two_solid()
