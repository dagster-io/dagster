from dagster import composite_solid
from dagster.legacy import pipeline, solid


@solid
def do_something():
    pass


@solid
def do_something_else():
    return 5


@composite_solid
def do_two_things():
    do_something()
    return do_something_else()


@solid
def do_yet_more(arg1):
    assert arg1 == 5


@pipeline
def do_it_all():
    do_yet_more(do_two_things())
