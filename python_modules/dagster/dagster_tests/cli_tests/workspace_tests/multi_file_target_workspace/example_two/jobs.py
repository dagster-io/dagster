import dagster as dg
from ops import example_two_op


@dg.job
def example_two_job():
    example_two_op()
