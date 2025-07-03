import dagster as dg


@dg.definitions
def defs() -> dg.Definitions:
    @dg.asset
    def asset1(): ...

    return dg.Definitions(assets=[asset1])
