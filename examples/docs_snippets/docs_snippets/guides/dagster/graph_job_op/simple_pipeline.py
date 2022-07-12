from dagster import pipeline
from dagster.legacy import solid


@solid
def do_something():
    ...


@pipeline
def do_it_all():
    do_something()
