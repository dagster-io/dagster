from dagster import graph, op, repository


@op
def my_op():
    return 5


@op
def ingest(x):
    return x + 5


@graph
def basic():
    ingest(my_op())


the_job = basic.to_job(name="the_job")


@repository
def basic_repo():
    return [the_job]
