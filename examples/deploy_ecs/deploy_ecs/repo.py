import time

from dagster import graph, op, repository


@op
def my_op():
    time.sleep(30)
    return True


@graph
def my_graph():
    my_op()


my_job = my_graph.to_job()


@repository
def repo():
    return [my_job]
