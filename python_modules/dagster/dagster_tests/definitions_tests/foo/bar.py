from dagster import job

from .baz import baz_op  # pylint: disable=import-error


@job
def bar_job():
    baz_op()
