from dagster import job

from .baz import baz_op


@job
def bar_job():
    baz_op()
