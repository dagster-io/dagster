import dagster as dg


@dg.asset
def bar():
    return None
