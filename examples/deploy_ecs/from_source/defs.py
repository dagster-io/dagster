import time

from dagster import Definitions, graph, op


@op
def my_op():
    time.sleep(30)
    return True


@graph
def my_graph():
    my_op()


my_job = my_graph.to_job()


defs = Definitions(jobs=[my_job])
