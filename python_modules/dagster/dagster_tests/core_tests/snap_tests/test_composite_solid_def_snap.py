from dagster import composite_solid, solid
from dagster.core.snap import (
    CompositeSolidDefSnap,
    DependencyStructureIndex,
    build_composite_solid_def_snap,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_noop_comp_solid_definition():
    @solid
    def noop_solid(_):
        pass

    @composite_solid
    def comp_solid():
        noop_solid()

    comp_solid_meta = build_composite_solid_def_snap(comp_solid)

    assert isinstance(comp_solid_meta, CompositeSolidDefSnap)
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(comp_solid_meta))
        == comp_solid_meta
    )


def test_basic_comp_solid_definition():
    @solid
    def return_one(_):
        return 1

    @solid
    def take_one(_, one):
        return one

    @composite_solid
    def comp_solid():
        take_one(return_one())

    comp_solid_meta = build_composite_solid_def_snap(comp_solid)

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
    @solid
    def return_one(_):
        return 1

    @solid
    def take_many(_, items):
        return items

    @composite_solid
    def comp_solid(this_number):
        take_many([return_one(), this_number, return_one.alias("return_one_also")()])

    comp_solid_meta = build_composite_solid_def_snap(comp_solid)

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
