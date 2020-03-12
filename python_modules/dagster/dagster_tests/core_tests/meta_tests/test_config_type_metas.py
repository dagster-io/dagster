from dagster import (
    Array,
    Field,
    ModeDefinition,
    Noneable,
    Selector,
    Shape,
    pipeline,
    resource,
    solid,
)
from dagster.config.field import resolve_to_config_type
from dagster.core.meta.config_types import (
    ConfigTypeKind,
    build_config_schema_snapshot,
    meta_from_config_type,
)
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def meta_from_dagster_type(dagster_type):
    return meta_from_config_type(resolve_to_config_type(dagster_type))


def test_basic_int_meta():
    int_meta = meta_from_dagster_type(int)
    assert int_meta.given_name == 'Int'
    assert int_meta.key == 'Int'
    assert int_meta.kind == ConfigTypeKind.SCALAR
    assert int_meta.enum_values is None
    assert int_meta.fields is None


def test_basic_dict():
    dict_meta = meta_from_dagster_type({'foo': int})
    assert dict_meta.key.startswith('Shape.')
    assert dict_meta.given_name is None
    child_type_keys = dict_meta.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == 'Int'
    assert child_type_keys[0]

    assert dict_meta.fields and len(dict_meta.fields) == 1

    field = dict_meta.fields[0]
    assert field.name == 'foo'


def test_field_things():
    dict_meta = meta_from_dagster_type(
        {
            'req': int,
            'opt': Field(int, is_required=False),
            'opt_with_default': Field(int, is_required=False, default_value=2),
            'req_with_desc': Field(int, description='A desc'),
        }
    )

    assert dict_meta.fields and len(dict_meta.fields) == 4

    field_meta_dict = {field_meta.name: field_meta for field_meta in dict_meta.fields}

    assert field_meta_dict['req'].is_required is True
    assert field_meta_dict['req'].description is None
    assert field_meta_dict['opt'].is_required is False
    assert field_meta_dict['opt_with_default'].is_required is False
    assert field_meta_dict['opt_with_default'].default_provided is True
    assert field_meta_dict['opt_with_default'].default_value_as_str == '2'

    assert field_meta_dict['req_with_desc'].is_required is True
    assert field_meta_dict['req_with_desc'].description == 'A desc'


def test_basic_list():
    list_meta = meta_from_dagster_type(Array(int))
    assert list_meta.key.startswith('Array')
    child_type_keys = list_meta.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == 'Int'


def test_basic_optional():
    optional_meta = meta_from_dagster_type(Noneable(int))
    assert optional_meta.key.startswith('Noneable')

    child_type_keys = optional_meta.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == 'Int'
    assert optional_meta.kind == ConfigTypeKind.NONEABLE
    assert optional_meta.enum_values is None


def test_basic_list_list():
    list_meta = meta_from_dagster_type([[int]])
    assert list_meta.key.startswith('Array')
    child_type_keys = list_meta.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0] == 'Array.Int'
    assert list_meta.enum_values is None


def test_list_of_dict():
    inner_dict_dagster_type = Shape({'foo': Field(str)})
    list_of_dict_meta = meta_from_dagster_type([inner_dict_dagster_type])

    assert list_of_dict_meta.key.startswith('Array')
    child_type_keys = list_of_dict_meta.get_child_type_keys()
    assert child_type_keys
    assert len(child_type_keys) == 1
    assert child_type_keys[0].startswith('Shape')


def test_selector_of_things():
    selector_meta = meta_from_dagster_type(Selector({'bar': Field(int)}))
    assert selector_meta.key.startswith('Selector')
    assert selector_meta.kind == ConfigTypeKind.SELECTOR
    assert selector_meta.fields and len(selector_meta.fields) == 1
    field_meta = selector_meta.fields[0]
    assert field_meta.name == 'bar'
    assert field_meta.type_key == 'Int'


def test_kitchen_sink():
    kitchen_sink = resolve_to_config_type(
        [
            {
                'opt_list_of_int': Field(int, is_required=False),
                'nested_dict': {
                    'list_list': [[int]],
                    'nested_selector': Field(
                        Selector({'some_field': int, 'more_list': Noneable([bool])})
                    ),
                },
            }
        ]
    )

    kitchen_sink_meta = meta_from_dagster_type(kitchen_sink)

    rehydrated_meta = deserialize_json_to_dagster_namedtuple(
        serialize_dagster_namedtuple(kitchen_sink_meta)
    )
    assert kitchen_sink_meta == rehydrated_meta


def test_simple_pipeline_smoke_test():
    @solid
    def solid_without_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_without_config()

    config_schema_snapshot = build_config_schema_snapshot(single_solid_pipeline)
    assert config_schema_snapshot.all_config_metas_by_key

    serialized = serialize_dagster_namedtuple(config_schema_snapshot)
    rehydrated_config_schema_snapshot = deserialize_json_to_dagster_namedtuple(serialized)
    assert config_schema_snapshot == rehydrated_config_schema_snapshot


def test_check_solid_config_correct():
    @solid(config={'foo': str})
    def solid_with_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_config()

    solid_config_key = solid_with_config.config_field.config_type.key

    config_metas = build_config_schema_snapshot(single_solid_pipeline).all_config_metas_by_key

    assert solid_config_key in config_metas

    solid_config_meta = config_metas[solid_config_key]

    assert solid_config_meta.kind == ConfigTypeKind.STRICT_SHAPE
    assert len(solid_config_meta.fields) == 1

    foo_field = solid_config_meta.fields[0]

    assert foo_field.name == 'foo'
    assert foo_field.type_key == 'String'


def test_check_solid_list_list_config_correct():
    @solid(config={'list_list_int': [[{'bar': int}]]})
    def solid_with_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_config()

    solid_config_key = solid_with_config.config_field.config_type.key

    config_metas = build_config_schema_snapshot(single_solid_pipeline).all_config_metas_by_key
    assert solid_config_key in config_metas
    solid_config_meta = config_metas[solid_config_key]

    assert solid_config_meta.kind == ConfigTypeKind.STRICT_SHAPE
    assert len(solid_config_meta.fields) == 1

    list_list_field = solid_config_meta.fields[0]

    list_list_type_key = list_list_field.type_key

    assert list_list_type_key.startswith('Array.Array.')

    list_list_type = config_metas[list_list_type_key]

    assert list_list_type.kind == ConfigTypeKind.ARRAY
    list_meta = config_metas[list_list_type.inner_type_key]
    assert list_meta.kind == ConfigTypeKind.ARRAY
    assert config_metas[list_meta.inner_type_key].kind == ConfigTypeKind.STRICT_SHAPE


def test_kitchen_sink_break_out():
    @solid(
        config=[
            {
                'opt_list_of_int': Field([int], is_required=False),
                'nested_dict': {
                    'list_list': [[int]],
                    'nested_selector': Selector(
                        {'some_field': int, 'noneable_list': Noneable([bool])}
                    ),
                },
            }
        ]
    )
    def solid_with_kitchen_sink_config(_):
        pass

    @pipeline
    def single_solid_pipeline():
        solid_with_kitchen_sink_config()

    config_metas = build_config_schema_snapshot(single_solid_pipeline).all_config_metas_by_key

    solid_config_key = solid_with_kitchen_sink_config.config_field.config_type.key
    assert solid_config_key in config_metas
    solid_config_meta = config_metas[solid_config_key]

    assert solid_config_meta.kind == ConfigTypeKind.ARRAY

    dict_within_list = config_metas[solid_config_meta.inner_type_key]

    assert len(dict_within_list.fields) == 2

    opt_field = dict_within_list.get_field('opt_list_of_int')

    assert opt_field.is_required is False
    assert config_metas[opt_field.type_key].kind == ConfigTypeKind.ARRAY

    nested_dict = config_metas[dict_within_list.get_field('nested_dict').type_key]
    assert len(nested_dict.fields) == 2
    nested_selector = config_metas[nested_dict.get_field('nested_selector').type_key]
    noneable_list_bool = config_metas[nested_selector.get_field('noneable_list').type_key]
    assert noneable_list_bool.kind == ConfigTypeKind.NONEABLE
    list_bool = config_metas[noneable_list_bool.inner_type_key]
    assert list_bool.kind == ConfigTypeKind.ARRAY


def test_multiple_modes():
    @solid
    def noop_solid(_):
        pass

    @resource(config={'a': int})
    def a_resource(_):
        pass

    @resource(config={'b': int})
    def b_resource(_):
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(name='mode_a', resource_defs={'resource': a_resource}),
            ModeDefinition(name='mode_b', resource_defs={'resource': b_resource}),
        ]
    )
    def modez():
        noop_solid()

    config_metas = build_config_schema_snapshot(modez).all_config_metas_by_key

    assert a_resource.config_field.config_type.key in config_metas
    assert b_resource.config_field.config_type.key in config_metas
