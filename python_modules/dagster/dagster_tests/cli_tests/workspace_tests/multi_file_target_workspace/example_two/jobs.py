# type: ignore

from dagster import job
from ops import example_two_op


@job
def example_two_job():
    example_two_op()
