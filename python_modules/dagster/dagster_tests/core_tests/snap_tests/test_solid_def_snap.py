from dagster import InputDefinition, OutputDefinition, solid
from dagster.core.snap.solid import build_core_solid_def_snap
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_basic_solid_definition():
    @solid
    def noop_solid(_):
        pass

    solid_snap = build_core_solid_def_snap(noop_solid)

    assert solid_snap
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(solid_snap))
        == solid_snap
    )


def test_solid_definition_kitchen_sink():
    @solid(
        input_defs=[
            InputDefinition("arg_one", str, description="desc1"),
            InputDefinition("arg_two", int),
        ],
        output_defs=[
            OutputDefinition(name="output_one", dagster_type=str),
            OutputDefinition(
                name="output_two", dagster_type=int, description="desc2", is_required=False
            ),
        ],
        config_schema={"foo": int},
        description="a description",
        tags={"a_tag": "yup"},
        required_resource_keys={"b_resource", "a_resource"},
    )
    def kitchen_sink_solid(_, arg_two, arg_one):  # out of order to test positional_inputs
        assert arg_one
        assert arg_two
        raise Exception("should not execute")

    kitchen_sink_solid_snap = build_core_solid_def_snap(kitchen_sink_solid)

    assert kitchen_sink_solid_snap
    assert kitchen_sink_solid_snap.name == "kitchen_sink_solid"
    assert len(kitchen_sink_solid_snap.input_def_snaps) == 2
    assert [inp.name for inp in kitchen_sink_solid_snap.input_def_snaps] == ["arg_one", "arg_two"]
    assert [inp.dagster_type_key for inp in kitchen_sink_solid_snap.input_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_solid_snap.get_input_snap("arg_one").description == "desc1"

    assert [out.name for out in kitchen_sink_solid_snap.output_def_snaps] == [
        "output_one",
        "output_two",
    ]

    assert [out.dagster_type_key for out in kitchen_sink_solid_snap.output_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_solid_snap.get_output_snap("output_two").description == "desc2"
    assert kitchen_sink_solid_snap.get_output_snap("output_two").is_required is False

    assert kitchen_sink_solid_snap.required_resource_keys == ["a_resource", "b_resource"]
    assert kitchen_sink_solid_snap.tags == {"a_tag": "yup"}
    assert kitchen_sink_solid.positional_inputs == ["arg_two", "arg_one"]

    assert (
        deserialize_json_to_dagster_namedtuple(
            serialize_dagster_namedtuple(kitchen_sink_solid_snap)
        )
        == kitchen_sink_solid_snap
    )
