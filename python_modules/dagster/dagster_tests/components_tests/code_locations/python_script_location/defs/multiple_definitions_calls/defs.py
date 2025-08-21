import dagster as dg


@dg.definitions
def defs_one():
    return dg.Definitions(assets=[dg.AssetSpec(key="from_defs_one")])


@dg.definitions
def defs_two():
    return dg.Definitions(assets=[dg.AssetSpec(key="from_defs_two")])
