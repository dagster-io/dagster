from dagster import Definitions, asset

assets = []
for i in range(4):

    @asset(name=f"a_asset_{i}", group_name="my_asset_group_1")
    def a_asset():
        pass

    @asset(
        name=f"b_asset_{i}",
        group_name="my_asset_group_2",
        non_argument_deps={f"a_asset_{i}"},
    )
    def b_asset():
        pass

    @asset(
        name=f"c_asset_{i}",
        group_name="my_asset_group_3",
        non_argument_deps={f"b_asset_{i}"},
    )
    def c_asset():
        pass

    assets += [a_asset, b_asset, c_asset]


defs = Definitions(assets=assets)