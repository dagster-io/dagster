import dagster as dg


@dg.op(name="invalid!op/name")
def invalid_op():
    pass
