# type: ignore

from ops import example_two_op
from dagster import job


@job
def example_two_job():
    example_two_op()
