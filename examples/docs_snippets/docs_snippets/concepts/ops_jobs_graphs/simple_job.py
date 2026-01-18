import dagster as dg


@dg.op
def return_five():
    return 5


@dg.op
def add_one(arg):
    return arg + 1


@dg.job
def do_stuff():
    add_one(return_five())
