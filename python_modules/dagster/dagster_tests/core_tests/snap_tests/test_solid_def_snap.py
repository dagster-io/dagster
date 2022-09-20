from dagster import In, Out, op
from dagster._core.snap.solid import build_core_solid_def_snap
from dagster._serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_basic_solid_definition():
    @op
    def noop_op(_):
        pass

    solid_snap = build_core_solid_def_snap(noop_op)

    assert solid_snap
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(solid_snap))
        == solid_snap
    )


def test_solid_definition_kitchen_sink():
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

    kitchen_sink_solid_snap = build_core_solid_def_snap(kitchen_sink_op)

    assert kitchen_sink_solid_snap
    assert kitchen_sink_solid_snap.name == "kitchen_sink_op"
    assert len(kitchen_sink_solid_snap.input_def_snaps) == 2
    assert [inp.name for inp in kitchen_sink_solid_snap.input_def_snaps] == [
        "arg_one",
        "arg_two",
    ]
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

    assert kitchen_sink_solid_snap.required_resource_keys == [
        "a_resource",
        "b_resource",
    ]
    assert kitchen_sink_solid_snap.tags == {"a_tag": "yup"}
    assert kitchen_sink_op.positional_inputs == ["arg_two", "arg_one"]

    assert (
        deserialize_json_to_dagster_namedtuple(
            serialize_dagster_namedtuple(kitchen_sink_solid_snap)
        )
        == kitchen_sink_solid_snap
    )
