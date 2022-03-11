from dagster import Out, graph, op
from dagster._core.definitions.output import GraphOut


@op
def do_something():
    pass


@op(out={"one": Out(int), "two": Out(int)})
def return_multi():
    return 1, 2


@graph(out={"one": GraphOut(), "two": GraphOut()})
def do_two_things():
    do_something()
    one, two = return_multi()
    return (one, two)


@op
def do_yet_more(arg1, arg2):
    assert arg1 == 1
    assert arg2 == 2


@graph
def do_it_all():
    one, two = do_two_things()
    do_yet_more(one, two)
