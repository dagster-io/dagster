from ops import example_two_op  # type: ignore

import dagster as dg


@dg.job
def example_two_job():
    example_two_op()
