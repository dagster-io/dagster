import dagster as dg
from ops import example_two_op  # type: ignore


@dg.job
def example_two_job():
    example_two_op()
