from dagster import job

from dagster_tests.definitions_tests.foo.baz import baz_op


@job
def bar_job():
    baz_op()
