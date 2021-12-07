from dagster import RunRequest, graph, op, pipeline, repository, sensor, solid


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


@sensor(job=the_job, minimum_interval_seconds=1)
def the_sensor():
    yield RunRequest(run_key=None, run_config={})


@repository
def basic_repo():
    return [the_job, the_pipeline, the_sensor]
