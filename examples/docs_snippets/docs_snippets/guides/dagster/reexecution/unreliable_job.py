from random import random

from dagster import in_process_executor, job, op


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


@job(executor_def=in_process_executor)
def unreliable_job():
    end(unreliable(start()))
