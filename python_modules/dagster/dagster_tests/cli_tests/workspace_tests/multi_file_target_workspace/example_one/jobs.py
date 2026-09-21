import dagster as dg
from ops import example_one_op


@dg.job
def example_one_job():
    example_one_op()
