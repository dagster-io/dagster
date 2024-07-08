import os
import sys
import time

from dagster import MAX_RUNTIME_SECONDS_TAG, job, op, repository

DEFAULT_TAGS = {MAX_RUNTIME_SECONDS_TAG: "4"}


@job(tags=DEFAULT_TAGS)
def noop_job():
    pass


@op
def crashy_op(_):
    os._exit(1)


@job(tags=DEFAULT_TAGS)
def crashy_job():
    crashy_op()


@op
def exity_op(_):
    sys.exit(1)


@job(tags=DEFAULT_TAGS)
def exity_job():
    exity_op()


@op(tags=DEFAULT_TAGS)
def sleepy_op(_):
    while True:
        time.sleep(0.1)


@job(tags=DEFAULT_TAGS)
def sleepy_job():
    sleepy_op()


@op
def slow_op(_):
    time.sleep(4)


@job(tags=DEFAULT_TAGS)
def slow_job():
    slow_op()


@op
def return_one(_):
    return 1


@op
def multiply_by_2(_, num):
    return num * 2


@op
def multiply_by_3(_, num):
    return num * 3


@op
def add(_, num1, num2):
    return num1 + num2


@job(tags=DEFAULT_TAGS)
def math_diamond():
    one = return_one()
    add(multiply_by_2(one), multiply_by_3(one))


@repository
def celery_test_repository():
    return [
        noop_job,
        crashy_job,
        exity_job,
        sleepy_job,
        slow_job,
        math_diamond,
    ]
