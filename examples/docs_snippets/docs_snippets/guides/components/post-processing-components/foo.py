import dagster as dg


@dg.asset
def foo():
    return None
