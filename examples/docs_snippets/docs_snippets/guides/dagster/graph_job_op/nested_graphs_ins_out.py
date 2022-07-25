from dagster import GraphOut, In, Out, graph, op


@op
def do_something():
    pass


@op
def one():
    return 1


@op(ins={"arg1": In(int)}, out=Out(int))
def do_something_else(arg1):
    return arg1


@graph(out=GraphOut())
def do_two_things(arg1):
    do_something()
    return do_something_else(arg1)


@op
def do_yet_more(arg1):
    assert arg1 == 1


@graph
def do_it_all():
    do_yet_more(do_two_things(one()))
