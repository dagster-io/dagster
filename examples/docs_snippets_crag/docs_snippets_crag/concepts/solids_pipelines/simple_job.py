from dagster import job, op


@op
def do_something():
    pass


@job
def do_stuff():
    do_something()
