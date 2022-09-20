from dagster import graph, op
from dagster._core.snap import (
    CompositeSolidDefSnap,
    DependencyStructureIndex,
    build_composite_solid_def_snap,
)
from dagster._serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_noop_comp_solid_definition():
    @op
    def noop_op(_):
        pass

    @graph
    def comp_graph():
        noop_op()

    comp_solid_meta = build_composite_solid_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, CompositeSolidDefSnap)
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(comp_solid_meta))
        == comp_solid_meta
    )


def test_basic_comp_solid_definition():
    @op
    def return_one(_):
        return 1

    @op
    def take_one(_, one):
        return one

    @graph
    def comp_graph():
        take_one(return_one())

    comp_solid_meta = build_composite_solid_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, CompositeSolidDefSnap)
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(comp_solid_meta))
        == comp_solid_meta
    )

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_one")
    assert index.get_upstream_output("take_one", "one").solid_name == "return_one"
    assert index.get_upstream_output("take_one", "one").output_name == "result"


def test_complex_comp_solid_definition():
    @op
    def return_one(_):
        return 1

    @op
    def take_many(_, items):
        return items

    @graph
    def comp_graph(this_number):
        take_many([return_one(), this_number, return_one.alias("return_one_also")()])

    comp_solid_meta = build_composite_solid_def_snap(comp_graph)

    assert isinstance(comp_solid_meta, CompositeSolidDefSnap)
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(comp_solid_meta))
        == comp_solid_meta
    )

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_many")
    assert index.get_upstream_outputs("take_many", "items")[0].solid_name == "return_one"
    assert index.get_upstream_outputs("take_many", "items")[1].solid_name == "return_one_also"
