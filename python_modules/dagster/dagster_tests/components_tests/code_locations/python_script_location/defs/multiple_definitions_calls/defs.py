from dagster import AssetSpec, Definitions, definitions


@definitions
def defs_one():
    return Definitions(assets=[AssetSpec(key="from_defs_one")])


@definitions
def defs_two():
    return Definitions(assets=[AssetSpec(key="from_defs_two")])
