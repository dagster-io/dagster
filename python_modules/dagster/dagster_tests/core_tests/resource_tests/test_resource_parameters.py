import sys
from typing import Any

import dagster as dg
import pytest
from dagster import ResourceDefinition
from dagster._check import ParameterCheckError


def test_filter_out_resources():
    @dg.op
    def requires_resource_a(context, a: dg.ResourceParam[str]):
        assert a
        assert context.resources.a
        assert not hasattr(context.resources, "b")

    @dg.op
    def requires_resource_b(context, b: dg.ResourceParam[str]):
        assert b
        assert not hasattr(context.resources, "a")
        assert context.resources.b

    @dg.op
    def not_resources(context):
        assert not hasattr(context.resources, "a")
        assert not hasattr(context.resources, "b")

    @dg.job(
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

    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op
    def consumes_resource_a(a: dg.ResourceParam[str]):
        assert a == "A"

    @dg.op
    def consumes_resource_b(b: dg.ResourceParam[str]):
        assert b == "B"

    @dg.job(
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


def test_ops_with_dependencies():
    completed = set()

    @dg.op
    def first_op(foo: dg.ResourceParam[str]):
        assert foo == "foo"
        completed.add("first_op")
        return "hello"

    @dg.op
    def second_op(foo: dg.ResourceParam[str], first_op_result: str):
        assert foo == "foo"
        assert first_op_result == "hello"
        completed.add("second_op")
        return first_op_result + " world"

    @dg.op
    def third_op():
        completed.add("third_op")
        return "!"

    # Ensure ordering of resource args doesn't matter
    @dg.op
    def fourth_op(context, second_op_result: str, foo: dg.ResourceParam[str], third_op_result: str):
        assert foo == "foo"
        assert second_op_result == "hello world"
        assert third_op_result == "!"
        completed.add("fourth_op")
        return second_op_result + third_op_result

    @dg.job(
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("foo")},
    )
    def op_dependencies_job():
        fourth_op(second_op_result=second_op(first_op()), third_op_result=third_op())

    assert op_dependencies_job.execute_in_process().success

    assert completed == {"first_op", "second_op", "third_op", "fourth_op"}


def test_assets():
    executed = {}

    @dg.asset
    def the_asset(context, foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        executed["the_asset"] = True
        return "hello"

    @dg.asset
    def the_other_asset(context, the_asset, foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        assert the_asset == "hello"
        executed["the_other_asset"] = True
        return "world"

    # Ensure ordering of resource args doesn't matter
    @dg.asset
    def the_third_asset(context, the_asset, foo: dg.ResourceParam[str], the_other_asset):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        assert the_asset == "hello"
        assert the_other_asset == "world"
        executed["the_third_asset"] = True

    transformed_assets = dg.with_resources(
        [the_asset, the_other_asset, the_third_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )

    assert dg.materialize(transformed_assets).success
    assert executed["the_asset"]
    assert executed["the_other_asset"]
    assert executed["the_third_asset"]


def test_multi_assets():
    executed = {}

    @dg.multi_asset(outs={"a": dg.AssetOut(key="asset_a"), "b": dg.AssetOut(key="asset_b")})
    def two_assets(context, foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        executed["two_assets"] = True
        return 1, 2

    transformed_assets = dg.with_resources(
        [two_assets],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_assets, dg.AssetsDefinition)

    assert dg.materialize([transformed_assets]).success
    assert executed["two_assets"]


def test_resource_not_provided():
    @dg.asset
    def consumes_nonexistent_resource(
        not_provided: dg.ResourceParam[str],
    ):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'not_provided' required by op 'consumes_nonexistent_resource'",
    ):
        dg.with_resources([consumes_nonexistent_resource], {})


def test_resource_class():
    resource_called = {}

    class MyResource(dg.ResourceDefinition):
        def __init__(self):
            super().__init__(resource_fn=lambda *_, **__: self)

        def do_something(self):
            resource_called["called"] = True

    @dg.op
    def do_something_op(my_resource: dg.ResourceParam[MyResource]):
        my_resource.do_something()

    @dg.job(resource_defs={"my_resource": MyResource()})
    def my_job():
        do_something_op()

    assert my_job.execute_in_process().success
    assert resource_called["called"]

    @dg.asset
    def consumes_nonexistent_resource_class(
        not_provided: dg.ResourceParam[MyResource],
    ):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "resource with key 'not_provided' required by op 'consumes_nonexistent_resource_class'"
        ),
    ):
        dg.with_resources([consumes_nonexistent_resource_class], {})


def test_both_decorator_and_argument_error():
    with pytest.raises(
        ParameterCheckError,
        match=(
            "Invariant violation for parameter Cannot specify resource requirements in both @asset"
            " decorator and as arguments to the decorated function"
        ),
    ):

        @dg.asset(required_resource_keys={"foo"})
        def my_asset(bar: dg.ResourceParam[Any]):
            pass

    with pytest.raises(
        ParameterCheckError,
        match=(
            "Invariant violation for parameter Cannot specify resource requirements in both"
            " @multi_asset decorator and as arguments to the decorated function"
        ),
    ):

        @dg.multi_asset(
            outs={"a": dg.AssetOut(key="asset_a"), "b": dg.AssetOut(key="asset_b")},
            required_resource_keys={"foo"},
        )
        def my_assets(bar: dg.ResourceParam[Any]):
            pass

    with pytest.raises(
        ParameterCheckError,
        match=(
            "Invariant violation for parameter Cannot specify resource requirements in both @op"
            " decorator and as arguments to the decorated function"
        ),
    ):

        @dg.op(required_resource_keys={"foo"})
        def my_op(bar: dg.ResourceParam[Any]):
            pass


def test_asset_with_structured_config():
    class AnAssetConfig(dg.Config):
        a_string: str
        an_int: int

    executed = {}

    @dg.asset
    def the_asset(context, config: AnAssetConfig, foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        assert context.op_execution_context.op_config["a_string"] == "foo"
        assert config.a_string == "foo"
        assert config.an_int == 2
        executed["the_asset"] = True

    transformed_asset = dg.with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_asset, dg.AssetsDefinition)

    assert dg.materialize(
        [transformed_asset],
        run_config={"ops": {"the_asset": {"config": {"a_string": "foo", "an_int": 2}}}},
    ).success
    assert executed["the_asset"]


# Disabled for Python versions <3.9 as builtin types do not support generics
# until Python 3.9, https://peps.python.org/pep-0585/
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9")
def test_no_err_builtin_annotations():
    # Ensures that we can use Python builtin types without causing any issues, see
    # https://github.com/dagster-io/dagster/issues/11541

    executed = {}

    @dg.asset
    def the_asset(context, foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        executed["the_asset"] = True
        return [{"hello": "world"}]

    @dg.asset
    def the_other_asset(context, the_asset: list[dict[str, str]], foo: dg.ResourceParam[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"
        assert the_asset == [{"hello": "world"}]
        executed["the_other_asset"] = True
        return "world"

    transformed_assets = dg.with_resources(
        [the_asset, the_other_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )

    assert dg.materialize(transformed_assets).success
    assert executed["the_asset"]
    assert executed["the_other_asset"]
