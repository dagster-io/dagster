from dagster import Output, OutputDefinition, composite_solid, pipeline
from dagster.legacy import solid


@solid
def do_something():
    pass


@solid(output_defs=[OutputDefinition(int, "one"), OutputDefinition(int, "two")])
def return_multi():
    yield Output(1, "one")
    yield Output(2, "two")


@composite_solid(
    output_defs=[OutputDefinition(int, "one"), OutputDefinition(int, "two")]
)
def do_two_things():
    do_something()
    one, two = return_multi()
    return {"one": one, "two": two}


@solid
def do_yet_more(arg1, arg2):
    assert arg1 == 1
    assert arg2 == 2


@pipeline
def do_it_all():
    one, two = do_two_things()
    do_yet_more(one, two)
