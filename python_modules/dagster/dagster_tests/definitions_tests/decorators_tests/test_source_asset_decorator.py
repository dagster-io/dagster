import pytest
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.observe import observe
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.io_manager import io_manager


def test_all_fields():
    StaticPartitionsDefinition(["a", "b", "c", "d"])

    @io_manager(required_resource_keys={"baz"})
    def foo_manager():
        pass

    @observable_source_asset(
        name="alpha",
        description="beta",
        key_prefix="delta",
        metadata={"epsilon": "gamma"},
        io_manager_key="lambda",
        io_manager_def=foo_manager,
        group_name="rho",
        auto_observe_interval_minutes=5,
    )
    def foo_source_asset(context):
        raise Exception("not executed")

    assert foo_source_asset.key == AssetKey(["delta", "alpha"])
    assert foo_source_asset.description == "beta"
    assert foo_source_asset.io_manager_key == "lambda"
    assert foo_source_asset.group_name == "rho"
    assert foo_source_asset.resource_defs == {"lambda": foo_manager}
    assert foo_source_asset.io_manager_def == foo_manager
    assert foo_source_asset.metadata == {"epsilon": MetadataValue.text("gamma")}
    assert foo_source_asset.auto_observe_interval_minutes == 5


def test_no_context_observable_asset():
    executed = {}

    @observable_source_asset
    def observable_asset_no_context():
        executed["yes"] = True
        return DataVersion("version-string")

    result = observe([observable_asset_no_context])
    assert result.success
    assert executed["yes"]


def test_key_and_name_args():
    @observable_source_asset(key=["apple", "banana"])
    def key_specified():
        ...

    assert key_specified.key == AssetKey(["apple", "banana"])
    assert key_specified.op.name == "apple__banana"

    @observable_source_asset(key_prefix=["apple", "banana"])
    def key_prefix_specified():
        ...

    assert key_prefix_specified.key == AssetKey(["apple", "banana", "key_prefix_specified"])
    assert key_prefix_specified.op.name == "apple__banana__key_prefix_specified"

    @observable_source_asset(name="peach")
    def name_specified():
        ...

    assert name_specified.key == AssetKey(["peach"])
    assert name_specified.op.name == "peach"

    @observable_source_asset(key_prefix=["apple", "banana"], name="peach")
    def key_prefix_and_name_specified():
        ...

    assert key_prefix_and_name_specified.key == AssetKey(["apple", "banana", "peach"])
    assert key_prefix_and_name_specified.op.name == "apple__banana__peach"

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot specify a name or key prefix for @observable_source_asset when the key argument is provided",
    ):

        @observable_source_asset(key_prefix=["apple", "banana"], key=["peach", "nectarine"])
        def key_prefix_and_key_specified():
            ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot specify a name or key prefix for @observable_source_asset when the key argument is provided",
    ):

        @observable_source_asset(name=["peach"], key=["peach", "nectarine"])
        def name_and_key_specified():
            ...
