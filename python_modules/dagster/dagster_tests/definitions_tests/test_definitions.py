import json

import pytest
from dagster import (
    Any,
    AssetKey,
    DependencyDefinition,
    GraphDefinition,
    In,
    Int,
    JobDefinition,
    NodeInvocation,
    Out,
    String,
    op,
)
from dagster._core.definitions import AssetMaterialization, Node, create_run_config_schema
from dagster._core.definitions.dependency import NodeHandle, NodeOutput
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG
from dagster._legacy import InputDefinition


def test_deps_equal():
    assert DependencyDefinition("foo") == DependencyDefinition("foo")
    assert DependencyDefinition("foo") != DependencyDefinition("bar")

    assert DependencyDefinition("foo", "bar") == DependencyDefinition("foo", "bar")
    assert DependencyDefinition("foo", "bar") != DependencyDefinition("foo", "quuz")


def test_op_def():
    @op
    def produce_string():
        return "foo"

    @op(
        ins={"input_one": In(String)},
        out=Out(Any),  # pyright: ignore[reportArgumentType]
        config_schema={"another_field": Int},
    )
    def op_one(_context, input_one):
        raise Exception("should not execute")

    job_def = GraphDefinition(
        node_defs=[produce_string, op_one],
        name="test",
        dependencies={"op_one": {"input_one": DependencyDefinition("produce_string")}},
    )

    assert len(list(job_def.nodes[0].outputs())) == 1

    assert isinstance(job_def.node_named("op_one"), Node)

    solid_one_solid = job_def.node_named("op_one")

    assert solid_one_solid.has_input("input_one")

    assert isinstance(solid_one_solid.input_def_named("input_one"), InputDefinition)

    assert len(solid_one_solid.input_dict) == 1
    assert len(solid_one_solid.output_dict) == 1

    assert (
        str(solid_one_solid.get_input("input_one"))
        == "NodeInput(input_name=\"'input_one'\", node_name=\"'op_one'\")"
    )

    assert (
        repr(solid_one_solid.get_input("input_one"))
        == "NodeInput(input_name=\"'input_one'\", node_name=\"'op_one'\")"
    )

    assert (
        str(solid_one_solid.get_output("result"))
        == "NodeOutput(node_name=\"'op_one'\", output_name=\"'result'\")"
    )

    assert (
        repr(solid_one_solid.get_output("result"))
        == "NodeOutput(node_name=\"'op_one'\", output_name=\"'result'\")"
    )

    assert solid_one_solid.get_output("result") == NodeOutput(
        solid_one_solid, solid_one_solid.output_dict["result"]
    )

    assert len(job_def.dependency_structure.input_to_upstream_outputs_for_node("op_one")) == 1

    assert (
        len(job_def.dependency_structure.output_to_downstream_inputs_for_node("produce_string"))
        == 1
    )

    assert len(job_def.dependency_structure.inputs()) == 1


def test_op_def_bad_input_name():
    with pytest.raises(DagsterInvalidDefinitionError, match='"context" is not a valid name'):

        @op(ins={"context": In(String)})
        def op_one(_, _context):
            pass


def test_op_def_receives_version():
    @op
    def op_no_version(_):
        pass

    assert op_no_version.version is None

    @op(version="42")
    def op_with_version(_):
        pass

    assert op_with_version.version == "42"


def test_job_types():
    @op
    def produce_string():
        return "foo"

    @op(
        ins={"input_one": In(String)},
        out=Out(Any),  # pyright: ignore[reportArgumentType]
        config_schema={"another_field": Int},
    )
    def op_one(_context, input_one):
        raise Exception("should not execute")

    job_def = JobDefinition(
        graph_def=GraphDefinition(
            node_defs=[produce_string, op_one],
            name="test",
            dependencies={"op_one": {"input_one": DependencyDefinition("produce_string")}},
        )
    )

    run_config_schema = create_run_config_schema(job_def)

    assert run_config_schema.has_config_type("String")
    assert run_config_schema.has_config_type("Int")
    assert not run_config_schema.has_config_type("SomeName")


def test_mapper_errors():
    @op
    def op_a():
        return 1

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_1:
        GraphDefinition(
            node_defs=[op_a],
            name="test",
            dependencies={"solid_b": {"arg_a": DependencyDefinition("op_a")}},
        )
    assert (
        str(excinfo_1.value)
        == 'Invalid dependencies: node "solid_b" in dependency dictionary not found in node list'
    )

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_2:
        GraphDefinition(
            node_defs=[op_a],
            name="test",
            dependencies={
                NodeInvocation("solid_b", alias="solid_c"): {"arg_a": DependencyDefinition("op_a")}
            },
        )
    assert (
        str(excinfo_2.value)
        == 'Invalid dependencies: node "solid_b" (aliased by "solid_c" in dependency dictionary)'
        " not found in node list"
    )


def test_materialization():
    assert isinstance(AssetMaterialization("foo", "foo.txt"), AssetMaterialization)


def test_materialization_assign_label_from_asset_key():
    mat = AssetMaterialization(asset_key=AssetKey(["foo", "bar"]))
    assert mat.label == "foo bar"


def test_rehydrate_op_handle():
    h = NodeHandle.from_dict({"name": "foo", "parent": None})
    assert h.name == "foo"
    assert h.parent is None

    h = NodeHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert h.parent is None

    h = NodeHandle.from_dict({"name": "foo", "parent": ["bar", None]})
    assert h.name == "foo"
    assert isinstance(h.parent, NodeHandle)
    assert h.parent.name == "bar"
    assert h.parent.parent is None

    h = NodeHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert isinstance(h.parent, NodeHandle)
    assert h.parent.name == "bar"
    assert h.parent.parent is None

    h = NodeHandle.from_dict({"name": "foo", "parent": ["bar", ["baz", None]]})
    assert h.name == "foo"
    assert isinstance(h.parent, NodeHandle)
    assert h.parent.name == "bar"
    assert isinstance(h.parent.parent, NodeHandle)
    assert h.parent.parent.name == "baz"
    assert h.parent.parent.parent is None

    h = NodeHandle.from_dict(json.loads(json.dumps(h._asdict())))
    assert h.name == "foo"
    assert isinstance(h.parent, NodeHandle)
    assert h.parent.name == "bar"
    assert isinstance(h.parent.parent, NodeHandle)
    assert h.parent.parent.name == "baz"
    assert h.parent.parent.parent is None


def test_cycle_detect():
    @op
    def return_one():
        return 1

    @op
    def add(a, b):
        return a + b

    with pytest.raises(DagsterInvalidDefinitionError, match="Circular dependencies exist"):
        GraphDefinition(
            node_defs=[return_one, add],
            name="test",
            dependencies={
                NodeInvocation("add", alias="first"): {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("second"),
                },
                NodeInvocation("add", alias="second"): {
                    "a": DependencyDefinition("first"),
                    "b": DependencyDefinition("return_one"),
                },
            },
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="Circular dependencies exist"):
        GraphDefinition(
            name="circletron",
            node_defs=[return_one, add],
            dependencies={
                NodeInvocation("add", alias="first"): {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("second"),
                },
                NodeInvocation("add", alias="second"): {
                    "a": DependencyDefinition("first"),
                    "b": DependencyDefinition("return_one"),
                },
            },
        )


def test_composite_mapping_collision():
    @op
    def return_one():
        return 1

    @op
    def add(a, b):
        return a + b

    with pytest.raises(DagsterInvalidDefinitionError, match="already satisfied by output"):
        GraphDefinition(
            name="add_one",
            node_defs=[return_one, add],
            input_mappings=[InputDefinition("val").mapping_to("add", "a")],
            dependencies={
                "add": {
                    "a": DependencyDefinition("return_one"),
                    "b": DependencyDefinition("return_one"),
                }
            },
        )


def test_pool_mismatch():
    with pytest.raises(DagsterInvalidDefinitionError) as _:

        @op(pool="foo", tags={GLOBAL_CONCURRENCY_TAG: "bar"})
        def my_op():
            pass


def test_pool_invalid():
    illegal_pools = ["foo/bar", "foo bar", "foo:bar", "foo,bar", "foo|bar", "foo.bar", "foo-bar"]
    for pool in illegal_pools:
        with pytest.raises(DagsterInvalidDefinitionError) as _:

            @op(pool=pool)
            def my_op():
                pass
