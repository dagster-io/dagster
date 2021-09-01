from random import random

from dagster import graph, op


@op
def start():
    return 1


@op
def unreliable(num: int) -> int:
    failure_rate = 0.5
    if random() < failure_rate:
        raise Exception("blah")

    return num


@op
def end(_num: int):
    pass


@graph
def unreliable_job():
    end(unreliable(start()))
