import dagster as dg


@dg.op
def step_one():
    ...


@dg.op
def step_two():
    ...


@dg.graph_asset
def complex_asset():
    return step_two(step_one())


defs = dg.Definitions(assets=[complex_asset])
