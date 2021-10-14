from dagster import graph, op, pipeline, repository, solid


@solid
def my_solid():
    return 5


@solid
def ingest_solid(x):
    return x + 5


@pipeline
def the_pipeline():
    ingest_solid(my_solid())


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
    return [the_job, the_pipeline]
