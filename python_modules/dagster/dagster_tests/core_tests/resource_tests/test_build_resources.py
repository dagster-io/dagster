import pytest
from dagster import Field, resource
from dagster.core.errors import DagsterResourceFunctionError
from dagster.core.execution.build_resources import init_resources


def test_basic_resource():
    @resource
    def basic_resource(_):
        return "foo"

    with init_resources(resource_defs={"basic_resource": basic_resource}) as resources:
        assert resources.resource_instance_dict["basic_resource"] == "foo"


def test_resource_with_config():
    @resource(
        config_schema={"plant": str, "animal": Field(str, is_required=False, default_value="dog")}
    )
    def basic_resource(init_context):
        plant = init_context.resource_config["plant"]
        animal = init_context.resource_config["animal"]
        return f"plant: {plant}, animal: {animal}"

    with init_resources(
        resource_defs={"basic_resource": basic_resource},
        run_config={"basic_resource": {"config": {"plant": "maple tree"}}},
    ) as resources:
        assert (
            resources.resource_instance_dict["basic_resource"] == "plant: maple tree, animal: dog"
        )


def test_resource_with_dependencies():
    @resource(config_schema={"animal": str})
    def no_deps(init_context):
        return init_context.resource_config["animal"]

    @resource(required_resource_keys={"no_deps"})
    def has_deps(init_context):
        return f"{init_context.resources.no_deps} is an animal."

    with init_resources(
        resource_defs={"no_deps": no_deps, "has_deps": has_deps},
        run_config={"no_deps": {"config": {"animal": "dog"}}},
    ) as resources:
        assert resources.resource_instance_dict["no_deps"] == "dog"
        assert resources.resource_instance_dict["has_deps"] == "dog is an animal."


def test_error_in_resource_initialization():
    @resource
    def i_will_fail(_):
        raise Exception("Failed.")

    with pytest.raises(
        DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition i_will_fail",
    ):
        with init_resources(resource_defs={"i_will_fail": i_will_fail}):
            pass
