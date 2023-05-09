import pytest
from dagster import (
    ConfigurableResource,
    asset,
    op,
)
from dagster._core.errors import (
    DagsterInvalidInvocationError,
)
from dagster._core.execution.context.invocation import build_op_context


def test_direct_op_invocation() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @op
    def my_op(context, my_resource: MyResource) -> str:
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
    def my_op(context, my_resource: MyResource, my_other_resource: MyResource) -> str:
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
    def my_wacky_addition_op(context, x: int, y: int, my_resource: MyResource) -> int:
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
    def my_asset(context, my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Just providing context is ok, we'll use the resource from the context
    assert my_asset(build_op_context(resources={"my_resource": MyResource(a_str="foo")})) == "foo"

    # Providing both context and resource is not ok, because we don't know which one to use
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Cannot provide resources in both context and kwargs",
    ):
        assert (
            my_asset(
                context=build_op_context(resources={"my_resource": MyResource(a_str="foo")}),
                my_resource=MyResource(a_str="foo"),
            )
            == "foo"
        )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert my_asset(context=build_op_context(), my_resource=MyResource(a_str="foo")) == "foo"

    # Providing resource  as arg is ok, we'll use that (we still need a context though)
    assert my_asset(build_op_context(), MyResource(a_str="foo")) == "foo"

    @asset
    def my_asset_no_context(my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_asset_no_context(build_op_context(resources={"my_resource": MyResource(a_str="foo")}))
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert my_asset_no_context(my_resource=MyResource(a_str="foo")) == "foo"


def test_direct_asset_invocation_with_inputs() -> None:
    class MyResource(ConfigurableResource):
        z: int

    @asset
    def my_wacky_addition_asset(context, x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Just providing context is ok, we'll use the resource from the context
    # We are successfully able to input x and y as args
    assert (
        my_wacky_addition_asset(build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5)
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    # We can input x and y as args
    assert my_wacky_addition_asset(build_op_context(), 10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_asset(build_op_context(), y=1, x=2, my_resource=MyResource(z=3)) == 6

    @asset
    def my_wacky_addition_asset_no_context(x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Providing context is ok, we just discard it and use the resource from the context
    # We can input x and y as args
    assert (
        my_wacky_addition_asset_no_context(
            build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset_no_context(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
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
    def an_asset(context, my_resource: NumResource, my_other_resource: NumResource) -> None:
        assert context.resources.my_resource.num == 1
        assert context.resources.my_other_resource.num == 2
        assert my_resource.num == 1
        assert my_other_resource.num == 2
        executed["yes"] = True

    an_asset(build_op_context(), NumResource(num=1), NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(
        build_op_context(), my_resource=NumResource(num=1), my_other_resource=NumResource(num=2)
    )
    assert executed["yes"]
    executed.clear()

    an_asset(
        my_other_resource=NumResource(num=2),
        my_resource=NumResource(num=1),
        context=build_op_context(),
    )
    assert executed["yes"]
    executed.clear()
