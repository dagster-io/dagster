import time

import dagster as dg


@dg.op
def first_op(context: dg.OpExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(20)
    context.log.info("First asset executing")


@dg.op
def second_op_that_waits(context: dg.OpExecutionContext):
    context.log.info("Second asset executing")


@dg.job(
    # highlight-start
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 1,
                },
            }
        }
    }
    # highlight-end
)
def tag_concurrency_job():
    first_op()
    second_op_that_waits()


defs = dg.Definitions(
    jobs=[tag_concurrency_job],
)
