# mypy: disable-error-code=attr-defined
from solids import example_two_solid  # pylint: disable=no-name-in-module

from dagster import job


@job
def example_two_job():
    example_two_solid()
