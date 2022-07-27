# type: ignore[attr-defined]
from solids import example_one_solid  # pylint: disable=no-name-in-module

from dagster._legacy import pipeline


@pipeline
def example_one_pipeline():
    example_one_solid()
