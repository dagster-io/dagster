import dagster as dg


class MyIOManager(dg.IOManager):
    def handle_output(self, context: dg.OutputContext, obj):
        assert False

    def load_input(self, context: dg.InputContext):
        return 5


def get_assets():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    return dg.with_resources(
        [asset1, asset2],
        resource_defs={
            "io_manager": dg.IOManagerDefinition.hardcoded_io_manager(MyIOManager())
        },
    )


assets = get_assets()


def load_single_asset_value():
    defs = dg.Definitions(assets=assets)

    # single_asset_start_marker

    asset1_value = defs.load_asset_value(dg.AssetKey("asset1"))

    # single_asset_end_marker

    del asset1_value


def load_multiple_asset_values():
    defs = dg.Definitions(assets=assets)

    # multiple_asset_start_marker

    with defs.get_asset_value_loader() as loader:
        asset1_value = loader.load_asset_value(dg.AssetKey("asset1"))
        asset2_value = loader.load_asset_value(dg.AssetKey("asset2"))

    # multiple_asset_end_marker

    del asset1_value
    del asset2_value
