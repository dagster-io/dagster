from dagster import job, In, Out, op, Int, repository


@op(ins={"num": In(Int)}, out=Out(Int))
def add_one(num):
    return num + 1


@op(ins={"num": In(Int)}, out=Out(Int))
def mult_two(num):
    return num * 2


@job
def math():
    mult_two(num=add_one())


@repository
def test_override_repository():
    return [math]
