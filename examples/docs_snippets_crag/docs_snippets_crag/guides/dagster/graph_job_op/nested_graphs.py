from dagster import graph, op


@op
def do_something():
    pass


@op
def do_something_else():
    return 5


@graph
def do_two_things():
    do_something()
    return do_something_else()


@op
def do_yet_more(arg1):
    assert arg1 == 5


@graph
def do_it_all():
    do_yet_more(do_two_things())
