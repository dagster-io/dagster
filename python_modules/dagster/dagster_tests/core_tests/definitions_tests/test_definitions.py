import json

import pytest
from dagster import (
    Any,
    AssetKey,
    CompositeSolidDefinition,
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    SolidInvocation,
    String,
    lambda_solid,
    solid,
)
from dagster.core.definitions import AssetMaterialization, Solid, create_run_config_schema
from dagster.core.definitions.dependency import SolidHandle, SolidOutputHandle
from dagster.core.errors import DagsterInvalidDefinitionError


def test_deps_equal():
    assert DependencyDefinition("foo") == DependencyDefinition("foo")
    assert DependencyDefinition("foo") != DependencyDefinition("bar")

    assert DependencyDefinition("foo", "bar") == DependencyDefinition("foo", "bar")
    assert DependencyDefinition("foo", "bar") != DependencyDefinition("foo", "quuz")


def test_solid_def():
    @lambda_solid
    def produce_string():
        return "foo"

    @solid(
        input_defs=[InputDefinition("input_one", String)],
        output_defs=[OutputDefinition(Any)],
        config_schema={"another_field": Int},
    )
    def solid_one(_context, input_one):
        raise Exception("should not execute")

    pipeline_def = PipelineDefinition(
        solid_defs=[produce_string, solid_one],
        name="test",
        dependencies={"solid_one": {"input_one": DependencyDefinition("produce_string")}},
    )

    assert len(pipeline_def.solids[0].output_handles()) == 1

    assert isinstance(pipeline_def.solid_named("solid_one"), Solid)

    solid_one_solid = pipeline_def.solid_named("solid_one")

    assert solid_one_solid.has_input("input_one")

    assert isinstance(solid_one_solid.input_def_named("input_one"), InputDefinition)

    assert len(solid_one_solid.input_dict) == 1
    assert len(solid_one_solid.output_dict) == 1

    assert str(solid_one_solid.input_handle("input_one")) == (
        "SolidInputHandle(input_name=\"'input_one'\", solid_name=\"'solid_one'\")"
    )

    assert repr(solid_one_solid.input_handle("input_one")) == (
        "SolidInputHandle(input_name=\"'input_one'\", solid_name=\"'solid_one'\")"
    )

    assert str(solid_one_solid.output_handle("result")) == (
        "SolidOutputHandle(output_name=\"'result'\", solid_name=\"'solid_one'\")"
    )

    assert repr(solid_one_solid.output_handle("result")) == (
        "SolidOutputHandle(output_name=\"'result'\", solid_name=\"'solid_one'\")"
    )

    assert solid_one_solid.output_handle("result") == SolidOutputHandle(
        solid_one_solid, solid_one_solid.output_dict["result"]
    )

    assert (
        len(pipeline_def.dependency_structure.input_to_upstream_outputs_for_solid("solid_one")) == 1
    )

    assert (
        len(
            pipeline_def.dependency_structure.output_to_downstream_inputs_for_solid(
                "produce_string"
            )
        )
        == 1
    )

    assert len(pipeline_def.dependency_structure.input_handles()) == 1


def test_solid_def_bad_input_name():
    with pytest.raises(DagsterInvalidDefinitionError, match='"context" is not a valid name'):
        # pylint: disable=unused-variable
        @solid(input_defs=[InputDefinition("context", String)])
        def solid_one(_, _context):
            pass


def test_solid_def_receives_version():
    @solid
    def solid_no_version(_):
        pass

    assert solid_no_version.version == None

    @solid(version="42")
    def solid_with_version(_):
        pass

    assert solid_with_version.version == "42"


def test_pipeline_types():
    @lambda_solid
    def produce_string():
        return "foo"

    @solid(
        input_defs=[InputDefinition("input_one", String)],
        output_defs=[OutputDefinition(Any)],
        config_schema={"another_field": Int},
    )
    def solid_one(_context, input_one):
        raise Exception("should not execute")

    pipeline_def = PipelineDefinition(
        solid_defs=[produce_string, solid_one],
        name="test",
        dependencies={"solid_one": {"input_one": DependencyDefinition("produce_string")}},
    )

    run_config_schema = create_run_config_schema(pipeline_def)

    assert run_config_schema.has_config_type("String")
    assert run_config_schema.has_config_type("Int")
    assert not run_config_schema.has_config_type("SomeName")


def test_mapper_errors():
    @lambda_solid
    def solid_a():
        return 1

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_1:
        PipelineDefinition(
            solid_defs=[solid_a],
            name="test",
            dependencies={"solid_b": {"arg_a": DependencyDefinition("solid_a")}},
        )
    assert (
        str(excinfo_1.value)
        == 'Invalid dependencies: solid "solid_b" in dependency dictionary not found in solid list'
    )

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_2:
        PipelineDefinition(
            solid_defs=[solid_a],
            name="test",
            dependencies={
                SolidInvocation("solid_b", alias="solid_c"): {
                    "arg_a": DependencyDefinition("solid_a")
                }
            },
        )
    assert (
        str(excinfo_2.value)
        == 'Invalid dependencies: solid "solid_b" (aliased by "solid_c" in dependency dictionary) not found in solid list'
    )


def test_materialization():
    assert isinstance(AssetMaterialization("foo", "foo.txt"), AssetMaterialization)


def test_materialization_assign_label_from_asset_key():
    mat = AssetMaterialization(asset_key=AssetKey(["foo", "bar"]))
    assert mat.label == "foo bar"


def test_rehydrate_solid_handle():
    h = SolidHandle.from_dict({"name": "foo", "parent": None})
    assert h.name == "foo"
    assert h.parent is None

    h = SolidHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert h.parent is None

    h = SolidHandle.from_dict({"name": "foo", "parent": ["bar", None]})
    assert h.name == "foo"
    assert isinstance(h.parent, SolidHandle)
    assert h.parent.name == "bar"
    assert h.parent.parent is None

    h = SolidHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert isinstance(h.parent, SolidHandle)
    assert h.parent.name == "bar"
    assert h.parent.parent is None

    h = SolidHandle.from_dict({"name": "foo", "parent": ["bar", ["baz", None]]})
    assert h.name == "foo"
    assert isinstance(h.parent, SolidHandle)
    assert h.parent.name == "bar"
    assert isinstance(h.parent.parent, SolidHandle)
    assert h.parent.parent.name == "baz"
    assert h.parent.parent.parent is None

    h = SolidHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert isinstance(h.parent, SolidHandle)
    assert h.parent.name == "bar"
    assert isinstance(h.parent.parent, SolidHandle)
    assert h.parent.parent.name == "baz"
    assert h.parent.parent.parent is None


def test_cycle_detect():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add(a, b):
        return a + b

    with pytest.raises(DagsterInvalidDefinitionError, match="Circular dependencies exist"):
        PipelineDefinition(
            solid_defs=[return_one, add],
            name="test",
            dependencies={
                SolidInvocation("add", alias="first"): {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("second"),
                },
                SolidInvocation("add", alias="second"): {
                    "a": DependencyDefinition("first"),
                    "b": DependencyDefinition("return_one"),
                },
            },
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="Circular dependencies exist"):
        CompositeSolidDefinition(
            name="circletron",
            solid_defs=[return_one, add],
            dependencies={
                SolidInvocation("add", alias="first"): {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("second"),
                },
                SolidInvocation("add", alias="second"): {
                    "a": DependencyDefinition("first"),
                    "b": DependencyDefinition("return_one"),
                },
            },
        )


def test_composite_mapping_collision():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid
    def add(a, b):
        return a + b

    with pytest.raises(DagsterInvalidDefinitionError, match="already satisfied by solid output"):
        CompositeSolidDefinition(
            name="add_one",
            solid_defs=[return_one, add],
            input_mappings=[InputDefinition("val").mapping_to("add", "a")],
            dependencies={
                "add": {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("return_one"),
                }
            },
        )
