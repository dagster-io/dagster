import tempfile
from contextlib import contextmanager

from dagster import (
    AssetKey,
    DagsterInstance,
    DailyPartitionsDefinition,
    IOManager,
    PartitionKeyRange,
    ResourceDefinition,
    SourceAsset,
    asset,
    fs_io_manager,
    io_manager,
    materialize,
    repository,
    resource,
    with_resources,
)
from dagster._core.test_utils import instance_for_test


def test_single_asset():
    @asset(io_manager_key="my_io_manager", metadata={"a": "b"})
    def asset1(): ...

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.asset_key == AssetKey("asset1")
            assert context.upstream_output.asset_key == AssetKey("asset1")  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.definition_metadata["a"] == "b"  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.op_def == asset1.op  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.name == "result"  # pyright: ignore[reportOptionalMemberAccess]
            assert context.dagster_type.typing_type == int
            return 5

    happenings = set()

    @io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    @contextmanager
    def my_io_manager():
        try:
            happenings.add("resource_inited")
            yield MyIOManager()
        finally:
            happenings.add("torn_down")

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"my_io_manager": my_io_manager})

    with repo.get_asset_value_loader() as loader:
        assert "resource_inited" not in happenings
        assert "torn_down" not in happenings
        value = loader.load_asset_value(AssetKey("asset1"), python_type=int)
        assert "resource_inited" in happenings
        assert "torn_down" not in happenings
        assert value == 5

    assert "torn_down" in happenings

    assert repo.load_asset_value(AssetKey("asset1"), python_type=int) == 5


def test_source_asset():
    asset1 = SourceAsset("asset1", io_manager_key="my_io_manager", metadata={"a": "b"})

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.asset_key == AssetKey("asset1")
            assert context.upstream_output.asset_key == AssetKey("asset1")  # pyright: ignore[reportOptionalMemberAccess]
            assert context.upstream_output.definition_metadata["a"] == "b"  # pyright: ignore[reportOptionalMemberAccess]
            assert context.dagster_type.typing_type == int
            return 5

    happenings = set()

    @io_manager  # pyright: ignore[reportCallIssue,reportArgumentType]
    @contextmanager
    def my_io_manager():
        try:
            happenings.add("resource_inited")
            yield MyIOManager()
        finally:
            happenings.add("torn_down")

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"my_io_manager": my_io_manager})

    with repo.get_asset_value_loader() as loader:
        assert "resource_inited" not in happenings
        assert "torn_down" not in happenings
        value = loader.load_asset_value(AssetKey("asset1"), python_type=int)
        assert "resource_inited" in happenings
        assert "torn_down" not in happenings
        assert value == 5

    assert "torn_down" in happenings

    assert repo.load_asset_value(AssetKey("asset1"), python_type=int) == 5


def test_resource_dependencies_and_config():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.resources.other_resource == "apple"
            assert context.resource_config["config_key"] == "config_val"  # pyright: ignore[reportOptionalSubscript]
            return 5

    @io_manager(required_resource_keys={"other_resource"}, config_schema={"config_key": str})
    def my_io_manager():
        return MyIOManager()

    @asset(io_manager_key="my_io_manager")
    def asset1(): ...

    @repository
    def repo():
        return with_resources(
            [asset1],
            resource_defs={
                "my_io_manager": my_io_manager.configured({"config_key": "config_val"}),
                "other_resource": ResourceDefinition.hardcoded_resource("apple"),
            },
        )

    with repo.get_asset_value_loader() as loader:
        value = loader.load_asset_value(AssetKey("asset1"))
        assert value == 5


def test_two_io_managers_same_resource_dep():
    happenings = set()

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.resources.other_resource == "apple"
            return context.asset_key.path[-1] + "_5"

    @io_manager(required_resource_keys={"other_resource"})
    def io_manager1():
        return MyIOManager()

    @io_manager(required_resource_keys={"other_resource"})
    def io_manager2():
        return MyIOManager()

    @resource
    def other_resource():
        assert "other_resource_inited" not in happenings
        happenings.add("other_resource_inited")
        return "apple"

    @asset(io_manager_key="io_manager1")
    def asset1(): ...

    @asset(io_manager_key="io_manager2")
    def asset2(): ...

    @repository
    def repo():
        return with_resources(
            [asset1, asset2],
            resource_defs={
                "io_manager1": io_manager1,
                "io_manager2": io_manager2,
                "other_resource": other_resource,
            },
        )

    with repo.get_asset_value_loader() as loader:
        assert loader.load_asset_value(AssetKey("asset1")) == "asset1_5"
        assert loader.load_asset_value(AssetKey("asset2")) == "asset2_5"


def test_default_io_manager():
    @asset
    def asset1():
        return 5

    @repository
    def repo():
        return [asset1]

    with DagsterInstance.ephemeral() as instance:
        materialize([asset1], instance=instance)

        with repo.get_asset_value_loader(instance=instance) as loader:
            value = loader.load_asset_value(AssetKey("asset1"), python_type=int)
            assert value == 5

        assert repo.load_asset_value(AssetKey("asset1"), python_type=int, instance=instance) == 5


def test_partition_key():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.partition_key == "2020-05-05"
            assert context.has_asset_partitions
            assert context.asset_partition_key_range == PartitionKeyRange(
                "2020-05-05", "2020-05-05"
            )
            assert context.asset_partition_keys == ["2020-05-05"]
            return 5

    @io_manager
    def my_io_manager():
        return MyIOManager()

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
    def asset1(): ...

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    with instance_for_test() as instance:
        with repo.get_asset_value_loader(instance=instance) as loader:
            value = loader.load_asset_value(AssetKey("asset1"), partition_key="2020-05-05")
            assert value == 5


def test_partitions_with_fs_io_manager():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        io_manager_def = fs_io_manager.configured({"base_dir": tmpdir_path})

        @asset(
            partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
            io_manager_def=io_manager_def,
        )
        def asset1():
            return 5

        materialize([asset1], partition_key="2020-05-05")

        @repository
        def repo():
            return [asset1]

        with repo.get_asset_value_loader() as loader:
            value = loader.load_asset_value(AssetKey("asset1"), partition_key="2020-05-05")
            assert value == 5


def test_io_manager_with_config():
    class MyIOManager(IOManager):
        def __init__(self, key):
            self.key = key

        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return self.key

    @io_manager(config_schema={"key": int})
    def my_io_manager(context):
        return MyIOManager(context.resource_config["key"])

    @asset
    def asset1(): ...

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    resource_config = {"io_manager": {"config": {"key": 5}}}
    with repo.get_asset_value_loader() as loader:
        value = loader.load_asset_value(AssetKey("asset1"), resource_config=resource_config)
        assert value == 5


def test_io_manager_resource_with_config():
    @resource(config_schema={"key": int})
    def io_resource(context):
        return context.resource_config["key"]

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return context.resources.io_resource

    @io_manager(required_resource_keys={"io_resource"})
    def my_io_manager():
        return MyIOManager()

    @asset
    def asset1(): ...

    @repository
    def repo():
        return with_resources(
            [asset1], resource_defs={"io_manager": my_io_manager, "io_resource": io_resource}
        )

    resource_config = {"io_resource": {"config": {"key": 5}}}
    with repo.get_asset_value_loader() as loader:
        value = loader.load_asset_value(AssetKey("asset1"), resource_config=resource_config)
        assert value == 5


def test_nested_resource_deps():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.resources.first_order == "bar"
            return context.asset_key.path[-1] + "_5"

    @io_manager(required_resource_keys={"first_order"})
    def the_io_manager():
        return MyIOManager()

    @resource
    def second_order():
        return "foo"

    @resource(required_resource_keys={"second_order"})
    def first_order(context):
        assert context.resources.second_order == "foo"
        return "bar"

    @asset(io_manager_key="the_io_manager")
    def asset1(): ...

    @repository
    def repo():
        return with_resources(
            [asset1],
            resource_defs={
                "the_io_manager": the_io_manager,
                "first_order": first_order,
                "second_order": second_order,
            },
        )

    with repo.get_asset_value_loader() as loader:
        assert loader.load_asset_value(AssetKey("asset1")) == "asset1_5"
