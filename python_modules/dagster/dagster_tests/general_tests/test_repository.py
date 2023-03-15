"""Repository of test pipelines.
"""

import pytest
from dagster import (
    AssetKey,
    GraphDefinition,
    Int,
    IOManager,
    JobDefinition,
    asset,
    graph,
    io_manager,
    job,
    multiprocess_executor,
    op,
    repository,
    resource,
    with_resources,
)
from dagster._check import CheckError


def define_empty_job():
    return JobDefinition(name="empty_job", graph_def=GraphDefinition(name="empty_graph"))


def define_simple_job():
    @op
    def return_two():
        return 2

    @job
    def simple_job():
        return_two()

    return simple_job


def define_with_resources_job():
    @resource(config_schema=Int)
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_schema=Int)
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config_schema={"num_one": Int, "num_two": Int})
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config["num_one"]
            + init_context.resource_config["num_two"]
        )

    @op(required_resource_keys={"modifier"})
    def apply_to_three(context):
        return context.resources.modifier(3)

    @graph
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


@repository
def dagster_test_repository():
    return [
        define_empty_job(),
        define_simple_job(),
        *define_with_resources_job(),
    ]


def test_repository_construction():
    assert dagster_test_repository


@repository
def empty_repository():
    return []


def test_invalid_repository():
    with pytest.raises(CheckError):

        @repository
        def invalid_repository(_invalid_arg: str):
            return []


def test_asset_value_loader():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert False

        def load_input(self, context):
            return 5

    @io_manager()
    def my_io_manager():
        return MyIOManager()

    @asset
    def asset1():
        ...

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    value = repo.load_asset_value(AssetKey("asset1"))
    assert value == 5


def test_asset_value_loader_with_config():
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
    def asset1():
        ...

    @repository
    def repo():
        return with_resources([asset1], resource_defs={"io_manager": my_io_manager})

    resource_config = {"io_manager": {"config": {"key": 5}}}
    value = repo.load_asset_value(AssetKey("asset1"), resource_config=resource_config)
    assert value == 5


def test_asset_value_loader_with_resources():
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
    def asset1():
        ...

    @repository
    def repo():
        return with_resources(
            [asset1], resource_defs={"io_manager": my_io_manager, "io_resource": io_resource}
        )

    resource_config = {"io_resource": {"config": {"key": 5}}}
    value = repo.load_asset_value(AssetKey("asset1"), resource_config=resource_config)
    assert value == 5
