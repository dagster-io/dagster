import dagster as dg


@dg.op
def foo():
    pass


@dg.job
def bar():
    foo()
