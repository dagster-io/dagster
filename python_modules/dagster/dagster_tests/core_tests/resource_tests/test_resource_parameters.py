from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.storage.mem_io_manager import InMemoryIOManager

from dagster import (
    ResourceDefinition,
    asset,
    job,
    op,
    resource,
    with_resources,
    AssetsDefinition,
)
from dagster._core.definitions.resource_output import ResourceOutput


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


def test_with_assets():
    @asset
    def the_asset(context, foo: ResourceOutput[str]):
        assert context.resources.foo == "blah"
        assert foo == "blah"

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    assert build_assets_job("the_job", [transformed_asset]).execute_in_process().success


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
