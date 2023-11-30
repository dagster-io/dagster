import asyncio

import pytest
from dagster import (
    AssetExecutionContext,
    ConfigurableResource,
    OpExecutionContext,
    Out,
    Output,
    asset,
    op,
)
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.context.invocation import build_asset_context, build_op_context


def test_direct_op_invocation() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @op
    def my_op(context: OpExecutionContext, my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Just providing context is ok, we'll use the resource from the context
    assert my_op(build_op_context(resources={"my_resource": MyResource(a_str="foo")})) == "foo"

    # Providing both context and resource is not ok, because we don't know which one to use
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Cannot provide resources in both context and kwargs",
    ):
        assert (
            my_op(
                context=build_op_context(resources={"my_resource": MyResource(a_str="foo")}),
                my_resource=MyResource(a_str="foo"),
            )
            == "foo"
        )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert my_op(context=build_op_context(), my_resource=MyResource(a_str="foo")) == "foo"

    # Providing resource only as positional arg is ok, we'll use that (we still need a context though)
    assert my_op(build_op_context(), MyResource(a_str="foo")) == "foo"

    @op
    def my_op_no_context(my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_op_no_context(build_op_context(resources={"my_resource": MyResource(a_str="foo")}))
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert my_op_no_context(my_resource=MyResource(a_str="foo")) == "foo"


def test_direct_op_invocation_multiple_resources() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @op
    def my_op(
        context: OpExecutionContext, my_resource: MyResource, my_other_resource: MyResource
    ) -> str:
        assert my_resource.a_str == "foo"
        assert my_other_resource.a_str == "bar"
        return my_resource.a_str

    # Just providing context is ok, we'll use both resources from the context
    assert (
        my_op(
            build_op_context(
                resources={
                    "my_resource": MyResource(a_str="foo"),
                    "my_other_resource": MyResource(a_str="bar"),
                }
            )
        )
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert (
        my_op(
            context=build_op_context(),
            my_resource=MyResource(a_str="foo"),
            my_other_resource=MyResource(a_str="bar"),
        )
        == "foo"
    )

    @op
    def my_op_no_context(my_resource: MyResource, my_other_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        assert my_other_resource.a_str == "bar"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_op_no_context(
            build_op_context(
                resources={
                    "my_resource": MyResource(a_str="foo"),
                    "my_other_resource": MyResource(a_str="bar"),
                }
            )
        )
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert (
        my_op_no_context(
            my_resource=MyResource(a_str="foo"), my_other_resource=MyResource(a_str="bar")
        )
        == "foo"
    )


def test_direct_op_invocation_with_inputs() -> None:
    class MyResource(ConfigurableResource):
        z: int

    @op
    def my_wacky_addition_op(
        context: OpExecutionContext, x: int, y: int, my_resource: MyResource
    ) -> int:
        return x + y + my_resource.z

    # Just providing context is ok, we'll use the resource from the context
    # We are successfully able to input x and y as args
    assert (
        my_wacky_addition_op(build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5)
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_op(build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2)
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    # We can input x and y as args
    assert my_wacky_addition_op(build_op_context(), 10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_op(build_op_context(), y=1, x=2, my_resource=MyResource(z=3)) == 6

    @op
    def my_wacky_addition_op_no_context(x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Providing context is ok, we just discard it and use the resource from the context
    # We can input x and y as args
    assert (
        my_wacky_addition_op_no_context(
            build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_op_no_context(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that
    # We can input x and y as args
    assert my_wacky_addition_op_no_context(10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_op_no_context(y=1, x=2, my_resource=MyResource(z=3)) == 6

    # Direct invocation is a little weird if the resource comes before an input,
    # but it still works as long as you use kwargs for the inputs or provide the resource explicitly
    @op
    def my_wacky_addition_op_resource_first(my_resource: MyResource, x: int, y: int) -> int:
        return x + y + my_resource.z

    # Here we have to use kwargs for x and y because we're not providing the resource explicitly
    assert (
        my_wacky_addition_op_resource_first(
            build_op_context(resources={"my_resource": MyResource(z=2)}), x=4, y=5
        )
        == 11
    )

    # Here we can just use args for x and y because we're providing the resource explicitly as an arg
    assert my_wacky_addition_op_resource_first(MyResource(z=2), 45, 53) == 100


def test_direct_asset_invocation() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @asset
    def my_asset(context: AssetExecutionContext, my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Just providing context is ok, we'll use the resource from the context
    assert (
        my_asset(build_asset_context(resources={"my_resource": MyResource(a_str="foo")})) == "foo"
    )

    # Providing both context and resource is not ok, because we don't know which one to use
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Cannot provide resources in both context and kwargs",
    ):
        assert (
            my_asset(
                context=build_asset_context(resources={"my_resource": MyResource(a_str="foo")}),
                my_resource=MyResource(a_str="foo"),
            )
            == "foo"
        )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert my_asset(context=build_asset_context(), my_resource=MyResource(a_str="foo")) == "foo"

    # Providing resource  as arg is ok, we'll use that (we still need a context though)
    assert my_asset(build_asset_context(), MyResource(a_str="foo")) == "foo"

    @asset
    def my_asset_no_context(my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_asset_no_context(build_asset_context(resources={"my_resource": MyResource(a_str="foo")}))
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert my_asset_no_context(my_resource=MyResource(a_str="foo")) == "foo"


def test_direct_asset_invocation_with_inputs() -> None:
    class MyResource(ConfigurableResource):
        z: int

    @asset
    def my_wacky_addition_asset(
        context: AssetExecutionContext, x: int, y: int, my_resource: MyResource
    ) -> int:
        return x + y + my_resource.z

    # Just providing context is ok, we'll use the resource from the context
    # We are successfully able to input x and y as args
    assert (
        my_wacky_addition_asset(
            build_asset_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset(
            build_asset_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    # We can input x and y as args
    assert (
        my_wacky_addition_asset(build_asset_context(), 10, 20, my_resource=MyResource(z=30)) == 60
    )
    # We can also input x and y as kwargs in this case
    assert (
        my_wacky_addition_asset(build_asset_context(), y=1, x=2, my_resource=MyResource(z=3)) == 6
    )

    @asset
    def my_wacky_addition_asset_no_context(x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Providing context is ok, we just discard it and use the resource from the context
    # We can input x and y as args
    assert (
        my_wacky_addition_asset_no_context(
            build_asset_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset_no_context(
            build_asset_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that
    # We can input x and y as args
    assert my_wacky_addition_asset_no_context(10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_asset_no_context(y=1, x=2, my_resource=MyResource(z=3)) == 6


def test_direct_op_invocation_plain_arg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @op
    def an_op(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_op(NumResource(num=1))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @op
    def an_op(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_op(my_resource=NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_plain_arg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_asset(NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_kwarg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_asset(my_resource=NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_many_resource_args() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource, my_other_resource: NumResource) -> None:
        assert my_resource.num == 1
        assert my_other_resource.num == 2
        executed["yes"] = True

    an_asset(NumResource(num=1), NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(my_resource=NumResource(num=1), my_other_resource=NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(my_other_resource=NumResource(num=2), my_resource=NumResource(num=1))
    assert executed["yes"]
    executed.clear()

    an_asset(NumResource(num=1), my_other_resource=NumResource(num=2))
    assert executed["yes"]


def test_direct_asset_invocation_many_resource_args_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(
        context: AssetExecutionContext, my_resource: NumResource, my_other_resource: NumResource
    ) -> None:
        assert context.resources.my_resource.num == 1
        assert context.resources.my_other_resource.num == 2
        assert my_resource.num == 1
        assert my_other_resource.num == 2
        executed["yes"] = True

    an_asset(build_asset_context(), NumResource(num=1), NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(
        build_asset_context(), my_resource=NumResource(num=1), my_other_resource=NumResource(num=2)
    )
    assert executed["yes"]
    executed.clear()

    an_asset(
        my_other_resource=NumResource(num=2),
        my_resource=NumResource(num=1),
        context=build_asset_context(),
    )
    assert executed["yes"]
    executed.clear()


def test_direct_invocation_output_metadata():
    @asset
    def my_asset(context):
        context.add_output_metadata({"foo": "bar"})

    @asset
    def my_other_asset(context):
        context.add_output_metadata({"baz": "qux"})

    ctx = build_asset_context()

    my_asset(ctx)
    assert ctx.get_output_metadata("result") == {"foo": "bar"}

    # context in unbound when used in another invocation. This allows the metadata to be
    # added in my_other_asset
    my_other_asset(ctx)


def test_async_assets_with_shared_context():
    @asset
    async def async_asset_one(context):
        assert context.asset_key.to_user_string() == "async_asset_one"
        await asyncio.sleep(0.01)
        return "one"

    @asset
    async def async_asset_two(context):
        assert context.asset_key.to_user_string() == "async_asset_two"
        await asyncio.sleep(0.01)
        return "two"

    # test that we can run two ops/assets with the same context at the same time without
    # overriding op/asset specific attributes
    ctx = build_asset_context()

    async def main():
        return await asyncio.gather(
            async_asset_one(ctx),
            async_asset_two(ctx),
        )

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=r"This context is currently being used to execute .* The context"
        r" cannot be used to execute another op until .* has finished executing",
    ):
        asyncio.run(main())


def test_direct_invocation_resource_context_manager():
    from dagster import resource

    class YieldedResource:
        def get_value(self):
            return 1

    @resource
    def yielding_resource(context):
        yield YieldedResource()

    @asset(required_resource_keys={"yielded_resource"})
    def my_asset(context):
        assert context.resources.yielded_resource.get_value() == 1

    with build_op_context(resources={"yielded_resource": yielding_resource}) as ctx:
        my_asset(ctx)


def test_context_bound_state_non_generator():
    @asset
    def my_asset(context):
        assert context._bound_properties is not None  # noqa: SLF001

    ctx = build_op_context()
    assert ctx._bound_properties is None  # noqa: SLF001

    my_asset(ctx)
    assert ctx._bound_properties is None  # noqa: SLF001
    assert ctx._invocation_properties is not None  # noqa: SLF001


def test_context_bound_state_generator():
    @op(out={"first": Out(), "second": Out()})
    def generator(context):
        assert context._bound_properties is not None  # noqa: SLF001
        yield Output("one", output_name="first")
        yield Output("two", output_name="second")

    ctx = build_op_context()

    result = list(generator(ctx))
    assert result[0].value == "one"
    assert result[1].value == "two"

    assert ctx._bound_properties is None  # noqa: SLF001
    assert ctx._invocation_properties is not None  # noqa: SLF001


def test_context_bound_state_async():
    @asset
    async def async_asset(context):
        assert context._bound_properties is not None  # noqa: SLF001
        assert context.asset_key.to_user_string() == "async_asset"
        await asyncio.sleep(0.01)
        return "one"

    ctx = build_asset_context()

    result = asyncio.run(async_asset(ctx))
    assert result == "one"

    assert ctx._bound_properties is None  # noqa: SLF001
    assert ctx._invocation_properties is not None  # noqa: SLF001


def test_context_bound_state_async_generator():
    @op(out={"first": Out(), "second": Out()})
    async def async_generator(context):
        assert context._bound_properties is not None  # noqa: SLF001
        yield Output("one", output_name="first")
        await asyncio.sleep(0.01)
        yield Output("two", output_name="second")

    ctx = build_op_context()

    async def get_results():
        res = []
        async for output in async_generator(ctx):
            res.append(output)
        return res

    result = asyncio.run(get_results())
    assert result[0].value == "one"
    assert result[1].value == "two"

    assert ctx._bound_properties is None  # noqa: SLF001
    assert ctx._invocation_properties is not None  # noqa: SLF001
