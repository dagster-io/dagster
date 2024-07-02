from dagster import op, job


@op
def foo():
    pass


@job
def bar():
    foo()
