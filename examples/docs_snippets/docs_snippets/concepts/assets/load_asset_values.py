from dagster import (
    AssetKey,
    Definitions,
    DynamicPartitionsDefinition,
    InputContext,
    IOManager,
    IOManagerDefinition,
    OutputContext,
    asset,
    job,
    op,
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

    partitions_def = DynamicPartitionsDefinition(name="partitions")

    @asset(partitions_def=partitions_def)
    def asset3():
        ...

    return with_resources(
        [asset1, asset2, asset3],
        resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
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


def load_partitioned_asset_dynamically():
    defs = Definitions(assets=assets)

    # partitioned_asset_dynamically_start_marker

    @op
    def dynamic_partition_loader(context, asset_key, partition_key):
        with defs.get_asset_value_loader(instance=context.instance) as loader:
            partition_value = loader.load_asset_value(
                AssetKey(asset_key),
                partition_key=partition_key,
            )

            return partition_value

    # partitioned_asset_dynamically_end_marker

    @job
    def adhoc_partition_load():
        """Job wrapper of dynamic_partition_loader."""
        dynamic_partition_loader()
