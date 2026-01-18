import time

import dagster as dg


@dg.op(
    # highlight-start
    tags={"dagster/concurrency_key": "database"}
    # highlight-end
)
def first_op(context: dg.OpExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(20)
    context.log.info("First asset executing")


@dg.op(
    # highlight-start
    tags={"dagster/concurrency_key": "database"}
    # highlight-end
)
def second_op_that_waits(context: dg.OpExecutionContext):
    context.log.info("Second asset executing")


@dg.job
def tag_concurrency_job():
    first_op()
    second_op_that_waits()


defs = dg.Definitions(
    jobs=[tag_concurrency_job],
)
