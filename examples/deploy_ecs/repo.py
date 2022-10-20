import time

import boto3

from dagster import graph, op, repository


@op
def my_op(context):
    for i in range(200):
        time.sleep(0.5)
        print(f"stdout {i}")
        if i % 1000 == 420:
            context.log.error(f"Error message seq={i}")
        elif i % 100 == 0:
            context.log.warning(f"Warning message seq={i}")
        elif i % 10 == 0:
            context.log.info(f"Info message seq={i}")
        else:
            context.log.debug(f"Debug message seq={i}")

    ecs = boto3.client("ecs")
    print(ecs.list_tasks())
    print(context.pipeline_run.tags)

    return True


@graph
def my_graph():
    my_op()


my_job = my_graph.to_job()


@repository
def repo():
    return [my_job]
