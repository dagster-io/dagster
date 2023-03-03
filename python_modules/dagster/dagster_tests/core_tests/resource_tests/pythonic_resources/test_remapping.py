import pytest
from dagster import (
    ConfigurableResource,
    Definitions,
    asset,
    job,
    op,
)
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
)


def test_remap_resource_args_ops() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    executed = {}

    # Remap the resource key "my_resource_foo" to the input "my_resource"
    @op(resource_key_argument_mapping={"my_resource_foo": "my_resource"})
    def an_op(my_resource: MyResource) -> None:
        assert my_resource.a_str == "foo"
        executed["yes"] = True

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'my_resource_foo' required by op 'an_op' was not provided",
    ):

        @job(resource_defs={"my_resource": MyResource(a_str="foo")})
        def my_non_working_job() -> None:
            an_op()

    @job(resource_defs={"my_resource_foo": MyResource(a_str="foo")})
    def my_job() -> None:
        an_op()

    assert my_job.execute_in_process().success
    assert executed["yes"]


def test_remap_resource_args_assets() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    executed = {}

    # Remap the resource key "my_resource_foo" to the input "my_resource"
    @asset(resource_key_argument_mapping={"my_resource_foo": "my_resource"})
    def an_asset(my_resource: MyResource) -> None:
        assert my_resource.a_str == "foo"
        executed["yes"] = True

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'my_resource_foo' required by op 'an_asset' was not provided",
    ):
        defs = Definitions(
            assets=[an_asset],
            resources={
                "my_resource": MyResource(a_str="foo"),
            },
        )

    defs = Definitions(
        assets=[an_asset],
        resources={
            "my_resource_foo": MyResource(a_str="foo"),
        },
    )
    defs.get_implicit_global_asset_job_def().execute_in_process()

    assert executed["yes"]
