import dagster as dg
import pytest
from dagster._core.definitions.resource_definition import IContainsGenerator


def test_basic_resource():
    @dg.resource
    def basic_resource(_):
        return "foo"

    with dg.build_resources(
        resources={"basic_resource": basic_resource},
    ) as resources:
        assert not isinstance(resources, IContainsGenerator)
        assert resources.basic_resource == "foo"


def test_resource_with_config():
    @dg.resource(
        config_schema={
            "plant": str,
            "animal": dg.Field(str, is_required=False, default_value="dog"),
        }
    )
    def basic_resource(init_context):
        plant = init_context.resource_config["plant"]
        animal = init_context.resource_config["animal"]
        return f"plant: {plant}, animal: {animal}"

    with dg.build_resources(
        resources={"basic_resource": basic_resource},
        resource_config={"basic_resource": {"config": {"plant": "maple tree"}}},
    ) as resources:
        assert resources.basic_resource == "plant: maple tree, animal: dog"


def test_resource_with_dependencies():
    @dg.resource(config_schema={"animal": str})
    def no_deps(init_context):
        return init_context.resource_config["animal"]

    @dg.resource(required_resource_keys={"no_deps"})
    def has_deps(init_context):
        return f"{init_context.resources.no_deps} is an animal."

    with dg.build_resources(
        resources={"no_deps": no_deps, "has_deps": has_deps},
        resource_config={"no_deps": {"config": {"animal": "dog"}}},
    ) as resources:
        assert resources.no_deps == "dog"
        assert resources.has_deps == "dog is an animal."


def test_error_in_resource_initialization():
    @dg.resource
    def i_will_fail(_):
        raise Exception("Failed.")

    with pytest.raises(
        dg.DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition i_will_fail",
    ):
        with dg.build_resources(resources={"i_will_fail": i_will_fail}):
            pass


# Ensure that build_resources can provide an instance to the initialization process of a resource.
def test_resource_init_requires_instance():
    @dg.resource
    def basic_resource(init_context):
        assert init_context.instance

    dg.build_resources({"basic_resource": basic_resource})


def test_resource_init_values():
    @dg.resource(required_resource_keys={"bar"})
    def foo_resource(init_context):
        assert init_context.resources.bar == "bar"
        return "foo"

    with dg.build_resources({"foo": foo_resource, "bar": "bar"}) as resources:
        assert resources.foo == "foo"
        assert resources.bar == "bar"


def test_context_manager_resource():
    tore_down = []

    @dg.resource
    def cm_resource(_):
        try:
            yield "foo"
        finally:
            tore_down.append("yes")

    with dg.build_resources({"cm_resource": cm_resource}) as resources:
        assert isinstance(resources, IContainsGenerator)
        assert resources.cm_resource == "foo"

    assert tore_down == ["yes"]
