from dagster import job, op


@op
def do_something():
    return "foo"


@job
def do_it_all():
    do_something()
