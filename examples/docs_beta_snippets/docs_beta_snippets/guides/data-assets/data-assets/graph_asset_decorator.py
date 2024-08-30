import dagster as dg


@dg.graph_asset
def complex_asset():
    @op
    def step_one(): ...

    @op
    def step_two(): ...

    step_one()
    step_two()
    return

defs = dg.Definitions(assets=[complex_asset])