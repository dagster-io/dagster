# type: ignore
from ops import example_one_op
from dagster import job


@job
def example_one_job():
    example_one_op()
