from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.storage.io_manager import io_manager


def test_all_fields():

    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @io_manager(required_resource_keys={"baz"})  # type: ignore
    def foo_manager():
        pass

    @observable_source_asset(
        name="alpha",
        description="beta",
        key_prefix="delta",
        metadata={"epsilon": "gamma"},
        io_manager_key="lambda",
        io_manager_def=foo_manager,
        partitions_def=partitions_def,
        group_name="rho",
    )
    def foo_source_asset(context):
        return {"foo": "bar"}

    assert foo_source_asset.key == AssetKey(["delta", "alpha"])
    assert foo_source_asset.description == "beta"
    assert foo_source_asset.io_manager_key == "lambda"
    assert foo_source_asset.partitions_def == partitions_def
    assert foo_source_asset.group_name == "rho"
    assert foo_source_asset.resource_defs == {"lambda": foo_manager}
    assert foo_source_asset.io_manager_def == foo_manager
    assert foo_source_asset.metadata == {"epsilon": MetadataValue.text("gamma")}
