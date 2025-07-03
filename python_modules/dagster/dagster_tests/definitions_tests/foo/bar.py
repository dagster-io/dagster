import dagster as dg

from dagster_tests.definitions_tests.foo.baz import baz_op


@dg.job
def bar_job():
    baz_op()
