from dagster import OutputDefinition, composite_solid
from dagster.core.definitions.input import InputDefinition
from dagster.legacy import pipeline, solid


@solid
def do_something():
    pass


@solid
def one():
    return 1


@solid(
    input_defs=[InputDefinition("arg1", int)],
    output_defs=[OutputDefinition(int)],
)
def do_something_else(arg1):
    return arg1


@composite_solid(
    input_defs=[InputDefinition("arg1", int)],
    output_defs=[OutputDefinition(int)],
)
def do_two_things(arg1):
    do_something()
    return do_something_else(arg1)


@solid
def do_yet_more(arg1):
    assert arg1 == 1


@pipeline
def do_it_all():
    do_yet_more(do_two_things(one()))
