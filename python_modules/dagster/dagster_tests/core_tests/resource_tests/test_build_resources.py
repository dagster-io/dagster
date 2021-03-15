import pytest
from dagster import Field, resource
from dagster.core.errors import DagsterResourceFunctionError
from dagster.core.execution.build_resources import build_resources
from dagster.core.instance import DagsterInstance
from dagster.core.storage.mem_io_manager import InMemoryIOManager


def test_basic_resource():
    @resource
    def basic_resource(_):
        return "foo"

    with DagsterInstance.ephemeral() as dagster_instance:
        with build_resources(
            resources={"basic_resource": basic_resource},
            instance=dagster_instance,
        ) as resources:
            assert resources.basic_resource == "foo"


def test_resource_with_config():
    @resource(
        config_schema={"plant": str, "animal": Field(str, is_required=False, default_value="dog")}
    )
    def basic_resource(init_context):
        plant = init_context.resource_config["plant"]
        animal = init_context.resource_config["animal"]
        return f"plant: {plant}, animal: {animal}"

    with DagsterInstance.ephemeral() as dagster_instance:
        with build_resources(
            resources={"basic_resource": basic_resource},
            instance=dagster_instance,
            run_config={"basic_resource": {"config": {"plant": "maple tree"}}},
        ) as resources:
            assert resources.basic_resource == "plant: maple tree, animal: dog"


def test_resource_with_dependencies():
    @resource(config_schema={"animal": str})
    def no_deps(init_context):
        return init_context.resource_config["animal"]

    @resource(required_resource_keys={"no_deps"})
    def has_deps(init_context):
        return f"{init_context.resources.no_deps} is an animal."

    with DagsterInstance.ephemeral() as dagster_instance:
        with build_resources(
            resources={"no_deps": no_deps, "has_deps": has_deps},
            instance=dagster_instance,
            run_config={"no_deps": {"config": {"animal": "dog"}}},
        ) as resources:
            assert resources.no_deps == "dog"
            assert resources.has_deps == "dog is an animal."


def test_error_in_resource_initialization():
    @resource
    def i_will_fail(_):
        raise Exception("Failed.")

    with DagsterInstance.ephemeral() as dagster_instance:
        with pytest.raises(
            DagsterResourceFunctionError,
            match="Error executing resource_fn on ResourceDefinition i_will_fail",
        ):
            with build_resources(resources={"i_will_fail": i_will_fail}, instance=dagster_instance):
                pass


# Ensure that build_resources can provide an instance to the initialization process of a resource.
def test_resource_init_requires_instance():
    @resource
    def basic_resource(init_context):
        assert init_context.instance

    with DagsterInstance.ephemeral() as instance:
        build_resources({"basic_resource": basic_resource}, instance)


def test_resource_init_values():
    @resource(required_resource_keys={"bar"})
    def foo_resource(init_context):
        assert init_context.resources.bar == "bar"
        return "foo"

    with DagsterInstance.ephemeral() as instance:
        with build_resources({"foo": foo_resource, "bar": "bar"}, instance) as resources:
            assert resources.foo == "foo"
            assert resources.bar == "bar"


def test_resource_init_io_manager():
    with DagsterInstance.ephemeral() as instance:
        build_resources({"io_manager": InMemoryIOManager}, instance)
