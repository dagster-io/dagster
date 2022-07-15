from dagster.legacy import pipeline, solid


@solid
def do_something():
    ...


@pipeline
def do_it_all():
    do_something()
