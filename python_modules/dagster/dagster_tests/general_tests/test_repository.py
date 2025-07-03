import dagster as dg

"""Repository of test jobs."""

import pytest
from dagster import Int, multiprocess_executor
from dagster._check import CheckError


def define_empty_job():
    return dg.JobDefinition(name="empty_job", graph_def=dg.GraphDefinition(name="empty_graph"))


def define_simple_job():
    @dg.op
    def return_two():
        return 2

    @dg.job
    def simple_job():
        return_two()

    return simple_job


def define_with_resources_job():
    @dg.resource(config_schema=Int)
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @dg.resource(config_schema=Int)
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @dg.resource(config_schema={"num_one": dg.Int, "num_two": dg.Int})
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config["num_one"]
            + init_context.resource_config["num_two"]
        )

    @dg.op(required_resource_keys={"modifier"})
    def apply_to_three(context):
        return context.resources.modifier(3)

    @dg.graph
    def my_graph():
        apply_to_three()

    adder_job = my_graph.to_job(name="adder_job", resource_defs={"modifier": adder_resource})
    multer_job = my_graph.to_job(name="multer_job", resource_defs={"modifier": multer_resource})
    double_adder_job = my_graph.to_job(
        name="double_adder_job", resource_defs={"modifier": double_adder_resource}
    )
    multi_job = my_graph.to_job(
        "multi_job", resource_defs={"modifier": adder_resource}, executor_def=multiprocess_executor
    )

    return [adder_job, multer_job, double_adder_job, multi_job]


@dg.repository
def dagster_test_repository():
    return [
        define_empty_job(),
        define_simple_job(),
        *define_with_resources_job(),
    ]


def test_repository_construction():
    assert dagster_test_repository


@dg.repository(metadata={"string": "foo", "integer": 123})
def metadata_repository():
    return []


def test_repository_metadata():
    assert metadata_repository.metadata == {
        "string": dg.TextMetadataValue("foo"),
        "integer": dg.IntMetadataValue(123),
    }


@dg.repository
def empty_repository():
    return []


def test_invalid_repository():
    with pytest.raises(CheckError):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def invalid_repository(_invalid_arg: str):
            return []


def test_asset_value_loader():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return 5

    @dg.io_manager()
    def my_io_manager():
        return MyIOManager()

    @dg.asset
    def asset1(): ...

    @dg.repository
    def repo():
        return dg.with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    value = repo.load_asset_value(dg.AssetKey("asset1"))
    assert value == 5


def test_asset_value_loader_with_config():
    class MyIOManager(dg.IOManager):
        def __init__(self, key):
            self.key = key

        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return self.key

    @dg.io_manager(config_schema={"key": int})
    def my_io_manager(context):
        return MyIOManager(context.resource_config["key"])

    @dg.asset
    def asset1(): ...

    @dg.repository
    def repo():
        return dg.with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    resource_config = {"io_manager": {"config": {"key": 5}}}
    value = repo.load_asset_value(dg.AssetKey("asset1"), resource_config=resource_config)
    assert value == 5


def test_asset_value_loader_with_resources():
    @dg.resource(config_schema={"key": int})
    def io_resource(context):
        return context.resource_config["key"]

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return context.resources.io_resource

    @dg.io_manager(required_resource_keys={"io_resource"})
    def my_io_manager():
        return MyIOManager()

    @dg.asset
    def asset1(): ...

    @dg.repository
    def repo():
        return dg.with_resources(
            [asset1], resource_defs={"io_manager": my_io_manager, "io_resource": io_resource}
        )

    resource_config = {"io_resource": {"config": {"key": 5}}}
    value = repo.load_asset_value(dg.AssetKey("asset1"), resource_config=resource_config)
    assert value == 5


def test_asset_value_loader_with_metadata():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            assert context.definition_metadata is not None
            return context.definition_metadata.get("return") or 5

    @dg.io_manager()
    def my_io_manager():
        return MyIOManager()

    @dg.asset
    def asset1(): ...

    @dg.asset(metadata={"return": 20})
    def asset2(): ...

    @dg.repository
    def repo():
        return dg.with_resources([asset1, asset2], resource_defs={"io_manager": my_io_manager})

    value = repo.load_asset_value(dg.AssetKey("asset1"))
    assert value == 5

    value = repo.load_asset_value(dg.AssetKey("asset1"), metadata={"return": 10})
    assert value == 10

    value = repo.load_asset_value(dg.AssetKey("asset2"))
    assert value == 5
