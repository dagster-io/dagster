# type: ignore
from dagster import job
from ops import example_one_op


@job
def example_one_job():
    example_one_op()
