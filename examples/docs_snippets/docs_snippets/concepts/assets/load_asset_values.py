from dagster import (
    AssetKey,
    Definitions,
    InputContext,
    IOManager,
    IOManagerDefinition,
    OutputContext,
    asset,
    with_resources,
)


class MyIOManager(IOManager):
    def handle_output(self, context: OutputContext, obj):
        assert False

    def load_input(self, context: InputContext):
        return 5


def get_assets():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    return with_resources(
        [asset1, asset2],
        resource_defs={
            "io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())
        },
    )


assets = get_assets()


def load_single_asset_value():
    defs = Definitions(assets=assets)

    # single_asset_start_marker

    asset1_value = defs.load_asset_value(AssetKey("asset1"))

    # single_asset_end_marker

    del asset1_value


def load_multiple_asset_values():
    defs = Definitions(assets=assets)

    # multiple_asset_start_marker

    with defs.get_asset_value_loader() as loader:
        asset1_value = loader.load_asset_value(AssetKey("asset1"))
        asset2_value = loader.load_asset_value(AssetKey("asset2"))

    # multiple_asset_end_marker

    del asset1_value
    del asset2_value
