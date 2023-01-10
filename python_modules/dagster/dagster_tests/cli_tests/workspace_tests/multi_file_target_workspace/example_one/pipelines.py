# mypy: disable-error-code=attr-defined
from dagster._legacy import pipeline
from solids import example_one_solid  # pylint: disable=no-name-in-module


@pipeline
def example_one_pipeline():
    example_one_solid()
