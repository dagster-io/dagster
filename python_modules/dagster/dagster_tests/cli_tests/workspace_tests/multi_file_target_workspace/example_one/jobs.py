from ops import example_one_op  # type: ignore

import dagster as dg


@dg.job
def example_one_job():
    example_one_op()
