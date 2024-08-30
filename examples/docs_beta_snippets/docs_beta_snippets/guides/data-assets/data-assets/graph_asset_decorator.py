import dagster as dg


@dg.op
def step_one():
    return 42


@dg.op
def step_two(num):
    return num**2


@dg.graph_asset
def complex_asset():
    return step_two(step_one())


defs = dg.Definitions(assets=[complex_asset])
