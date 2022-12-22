from typing import Any

import pytest

from dagster import AssetsDefinition, ResourceDefinition, asset, job, op, resource, with_resources
from dagster._check import ParameterCheckError
from dagster._config.structured_config import Config
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.resource_output import ResourceOutput
from dagster._core.errors import DagsterInvalidDefinitionError


def test_filter_out_resources():
    @op
    def requires_resource_a(context, a: ResourceOutput[str]):
        assert a
        assert context.resources.a
        assert not hasattr(context.resources, "b")

    @op
    def requires_resource_b(context, b: ResourceOutput[str]):
        assert b
        assert not hasattr(context.resources, "a")
        assert context.resources.b

    @op
    def not_resources(context):
        assert not hasattr(context.resources, "a")
        assert not hasattr(context.resources, "b")

    @job(
        resource_defs={
            "a": ResourceDefinition.hardcoded_resource("foo"),
            "b": ResourceDefinition.hardcoded_resource("bar"),
        },
    )
    def room_of_requirement():
        requires_resource_a()
        requires_resource_b()
        not_resources()

    room_of_requirement.execute_in_process()


def test_init_resources():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @op
    def consumes_resource_a(a: ResourceOutput[str]):
        assert a == "A"

    @op
    def consumes_resource_b(b: ResourceOutput[str]):
        assert b == "B"

    @job(
        resource_defs={
            "a": resource_a,
            "b": resource_b,
        },
    )
    def selective_init_test_job():
        consumes_resource_a()
        consumes_resource_b()

    assert selective_init_test_job.execute_in_process().success

    assert set(resources_initted.keys()) == {"a", "b"}


def test_assets():
    executed = {}

    @asset
    def the_asset(context, foo: ResourceOutput[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        executed["the_asset"] = True

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    assert build_assets_job("the_job", [transformed_asset]).execute_in_process().success
    assert executed["the_asset"]


def test_multi_assets():
    executed = {}

    @multi_asset(outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")})
    def two_assets(context, foo: ResourceOutput[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        executed["two_assets"] = True
        return 1, 2

    transformed_assets = with_resources(
        [two_assets],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_assets, AssetsDefinition)

    assert build_assets_job("the_job", [transformed_assets]).execute_in_process().success
    assert executed["two_assets"]


def test_resource_not_provided():
    @asset
    def consumes_nonexistent_resource(
        not_provided: ResourceOutput[str],  # pylint: disable=unused-argument
    ):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'not_provided' required by op 'consumes_nonexistent_resource'",
    ):
        with_resources([consumes_nonexistent_resource], {})


def test_resource_class():

    resource_called = {}

    class MyResource(ResourceDefinition):
        def __init__(self):
            super().__init__(resource_fn=lambda *_, **__: self)

        def do_something(self):
            resource_called["called"] = True

    @op
    def do_something_op(my_resource: MyResource):
        my_resource.do_something()

    @job(resource_defs={"my_resource": MyResource()})
    def my_job():
        do_something_op()

    assert my_job.execute_in_process().success
    assert resource_called["called"]

    @asset
    def consumes_nonexistent_resource_class(
        not_provided: MyResource,  # pylint: disable=unused-argument
    ):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'not_provided' required by op 'consumes_nonexistent_resource_class'",
    ):
        with_resources([consumes_nonexistent_resource_class], {})


def test_both_decorator_and_argument_error():
    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements in both @asset decorator and as arguments to the decorated function",
    ):

        @asset(required_resource_keys={"foo"})
        def my_asset(bar: ResourceOutput[Any]):
            pass

    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements in both @multi_asset decorator and as arguments to the decorated function",
    ):

        @multi_asset(
            outs={"a": AssetOut(key="asset_a"), "b": AssetOut(key="asset_b")},
            required_resource_keys={"foo"},
        )
        def my_assets(bar: ResourceOutput[Any]):
            pass

    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements in both @op decorator and as arguments to the decorated function",
    ):

        @op(required_resource_keys={"foo"})
        def my_op(bar: ResourceOutput[Any]):
            pass


def test_asset_with_structured_config():
    class AnAssetConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @asset
    def the_asset(context, config: AnAssetConfig, foo: ResourceOutput[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        assert context.op_config["a_string"] == "foo"
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["the_asset"] = True

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    assert (
        build_assets_job(
            "the_job",
            [transformed_asset],
            config={"ops": {"the_asset": {"config": {"a_string": "foo", "an_int": 2}}}},
        )
        .execute_in_process()
        .success
    )
    assert executed["the_asset"]
