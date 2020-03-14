from dagster import InputDefinition, OutputDefinition, solid
from dagster.core.meta.solid import build_solid_def_meta
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_basic_solid_definition():
    @solid
    def noop_solid(_):
        pass

    solid_meta = build_solid_def_meta(noop_solid)

    assert solid_meta
    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(solid_meta))
        == solid_meta
    )


def test_solid_definition_kitchen_sink():
    @solid(
        input_defs=[
            InputDefinition('arg_one', str, description='desc1'),
            InputDefinition('arg_two', int),
        ],
        output_defs=[
            OutputDefinition(name='output_one', dagster_type=str),
            OutputDefinition(
                name='output_two', dagster_type=int, description='desc2', is_required=False
            ),
        ],
        config={'foo': int},
        description='a description',
        tags={'a_tag': 'yup'},
        required_resource_keys={'a_resource'},
    )
    def kitchen_sink_solid(_, arg_two, arg_one):  # out of order to test positional_inputs
        assert arg_one
        assert arg_two
        raise Exception('should not execute')

    kitchen_sink_solid_meta = build_solid_def_meta(kitchen_sink_solid)

    assert kitchen_sink_solid_meta
    assert kitchen_sink_solid_meta.name == 'kitchen_sink_solid'
    assert len(kitchen_sink_solid_meta.input_def_metas) == 2
    assert [inp.name for inp in kitchen_sink_solid_meta.input_def_metas] == ['arg_one', 'arg_two']
    assert [inp.dagster_type_key for inp in kitchen_sink_solid_meta.input_def_metas] == [
        'String',
        'Int',
    ]

    assert kitchen_sink_solid_meta.get_input_meta('arg_one').description == 'desc1'

    assert [out.name for out in kitchen_sink_solid_meta.output_def_metas] == [
        'output_one',
        'output_two',
    ]

    assert [out.dagster_type_key for out in kitchen_sink_solid_meta.output_def_metas] == [
        'String',
        'Int',
    ]

    assert kitchen_sink_solid_meta.get_output_meta('output_two').description == 'desc2'
    assert kitchen_sink_solid_meta.get_output_meta('output_two').is_required is False

    assert (
        kitchen_sink_solid_meta.config_field_meta.type_key
        == kitchen_sink_solid.config_field.config_type.key
    )

    assert kitchen_sink_solid_meta.required_resource_keys == ['a_resource']
    assert kitchen_sink_solid_meta.tags == {'a_tag': 'yup'}
    assert kitchen_sink_solid.positional_inputs == ['arg_two', 'arg_one']

    assert (
        deserialize_json_to_dagster_namedtuple(
            serialize_dagster_namedtuple(kitchen_sink_solid_meta)
        )
        == kitchen_sink_solid_meta
    )
