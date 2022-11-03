# mypy: disable-error-code=attr-defined
from solids import example_one_solid  # pylint: disable=no-name-in-module

from dagster import job


@job
def example_one_job():
    example_one_solid()
