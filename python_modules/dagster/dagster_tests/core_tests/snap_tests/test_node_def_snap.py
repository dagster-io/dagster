from dagster import In, Out, graph, op
from dagster._core.snap import (
    DependencyStructureIndex,
    GraphDefSnap,
    build_graph_def_snap,
)
from dagster._core.snap.node import OpDefSnap, build_op_def_snap
from dagster._serdes import serialize_value
from dagster._serdes.serdes import deserialize_value


def test_basic_op_definition():
    @op
    def noop_op(_):
        pass

    op_snap = build_op_def_snap(noop_op)

    assert op_snap
    assert deserialize_value(serialize_value(op_snap), OpDefSnap) == op_snap


def test_op_definition_kitchen_sink(ignore_code_origin):
    @op(
        ins={"arg_one": In(str, description="desc1"), "arg_two": In(int)},
        out={
            "output_one": Out(dagster_type=str),
            "output_two": Out(
                dagster_type=int,
                description="desc2",
                is_required=False,
            ),
        },
        config_schema={"foo": int},
        description="a description",
        tags={"a_tag": "yup"},
        required_resource_keys={"b_resource", "a_resource"},
    )
    def kitchen_sink_op(_, arg_two, arg_one):  # out of order to test positional_inputs
        assert arg_one
        assert arg_two
        raise Exception("should not execute")

    kitchen_sink_op_snap = build_op_def_snap(kitchen_sink_op)

    assert kitchen_sink_op_snap
    assert kitchen_sink_op_snap.name == "kitchen_sink_op"
    assert len(kitchen_sink_op_snap.input_def_snaps) == 2
    assert [inp.name for inp in kitchen_sink_op_snap.input_def_snaps] == [
        "arg_one",
        "arg_two",
    ]
    assert [inp.dagster_type_key for inp in kitchen_sink_op_snap.input_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_op_snap.get_input_snap("arg_one").description == "desc1"

    assert [out.name for out in kitchen_sink_op_snap.output_def_snaps] == [
        "output_one",
        "output_two",
    ]

    assert [out.dagster_type_key for out in kitchen_sink_op_snap.output_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_op_snap.get_output_snap("output_two").description == "desc2"
    assert kitchen_sink_op_snap.get_output_snap("output_two").is_required is False

    assert kitchen_sink_op_snap.required_resource_keys == [
        "a_resource",
        "b_resource",
    ]
    assert kitchen_sink_op_snap.tags == {"a_tag": "yup"}
    assert kitchen_sink_op.positional_inputs == ["arg_two", "arg_one"]

    assert (
        deserialize_value(serialize_value(kitchen_sink_op_snap), OpDefSnap) == kitchen_sink_op_snap
    )


def test_noop_graph_definition():
    @op
    def noop_op(_):
        pass

    @graph
    def comp_graph():
        noop_op()

    comp_solid_meta = build_graph_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert deserialize_value(serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta


def test_basic_graph_definition():
    @op
    def return_one(_):
        return 1

    @op
    def take_one(_, one):
        return one

    @graph
    def comp_graph():
        take_one(return_one())

    comp_solid_meta = build_graph_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert deserialize_value(serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_one")
    assert index.get_upstream_output("take_one", "one").node_name == "return_one"
    assert index.get_upstream_output("take_one", "one").output_name == "result"


def test_complex_graph_definition():
    @op
    def return_one(_):
        return 1

    @op
    def take_many(_, items):
        return items

    @graph
    def comp_graph(this_number):
        take_many([return_one(), this_number, return_one.alias("return_one_also")()])

    comp_solid_meta = build_graph_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert deserialize_value(serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_many")
    assert index.get_upstream_outputs("take_many", "items")[0].node_name == "return_one"
    assert index.get_upstream_outputs("take_many", "items")[1].node_name == "return_one_also"
