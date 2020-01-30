from dagster import Array, Field, Noneable, Selector, Shape
from dagster.config.field import resolve_to_config_type
from dagster.core.meta.config_types import (
    ConfigTypeKind,
    ConfigTypeMeta,
    NonGenericTypeRefMeta,
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
    assert int_meta.inner_type_refs == []
    assert int_meta.enum_values is None
    assert int_meta.fields is None


def test_basic_dict():
    dict_meta = meta_from_dagster_type({'foo': int})
    assert dict_meta.key.startswith('Shape.')
    assert dict_meta.given_name is None
    assert dict_meta.inner_type_refs
    assert len(dict_meta.inner_type_refs) == 1
    assert dict_meta.inner_type_refs[0].key == 'Int'
    assert dict_meta.enum_values is None

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

    assert field_meta_dict['req'].is_optional is False
    assert field_meta_dict['req'].description is None
    assert field_meta_dict['opt'].is_optional is True
    assert field_meta_dict['opt_with_default'].is_optional is True
    assert field_meta_dict['opt_with_default'].default_provided is True
    assert field_meta_dict['opt_with_default'].default_value_as_str == '2'

    assert field_meta_dict['req_with_desc'].is_optional is False
    assert field_meta_dict['req_with_desc'].description == 'A desc'


def test_basic_list():
    list_meta = meta_from_dagster_type(Array(int))
    assert list_meta.key.startswith('Array')
    assert list_meta.inner_type_refs
    assert len(list_meta.inner_type_refs) == 1
    assert list_meta.inner_type_refs[0].key == 'Int'
    assert list_meta.enum_values is None


def test_basic_optional():
    optional_meta = meta_from_dagster_type(Noneable(int))
    assert optional_meta.key.startswith('Noneable')
    assert optional_meta.inner_type_refs
    assert len(optional_meta.inner_type_refs) == 1
    assert optional_meta.inner_type_refs[0].key == 'Int'
    # https://github.com/dagster-io/dagster/issues/1933
    # TODO reconcile names
    assert optional_meta.kind == ConfigTypeKind.NONEABLE
    assert optional_meta.enum_values is None


def test_basic_list_list():
    list_meta = meta_from_dagster_type([[int]])
    assert list_meta.key.startswith('Array')
    assert list_meta.inner_type_refs
    assert len(list_meta.inner_type_refs) == 2
    refs = {ref.key: ref for ref in list_meta.inner_type_refs}
    assert (
        len(refs['Array.Int'].inner_type_refs) == 1
        and isinstance(refs['Array.Int'], ConfigTypeMeta)
        and refs['Array.Int'].inner_type_refs[0].key == 'Int'
    )
    assert refs['Int'].key == 'Int'
    assert list_meta.enum_values is None

    assert (
        len(list_meta.type_param_refs) == 1
        and list_meta.type_param_refs[0].kind == ConfigTypeKind.ARRAY
    )


def test_list_of_dict():
    inner_dict_dagster_type = Shape({'foo': Field(str)})
    list_of_dict_meta = meta_from_dagster_type([inner_dict_dagster_type])

    assert list_of_dict_meta.key.startswith('Array')
    assert list_of_dict_meta.inner_type_refs
    assert len(list_of_dict_meta.inner_type_refs) == 1
    # Both Shape[...] and str are NonGenericTypeRefMetas in this schema
    dict_ref = list_of_dict_meta.type_param_refs[0]
    assert isinstance(dict_ref, NonGenericTypeRefMeta)
    assert dict_ref.key.startswith('Shape')

    assert (
        len(list_of_dict_meta.type_param_refs) == 1
        and list_of_dict_meta.type_param_refs[0].key
        == resolve_to_config_type(inner_dict_dagster_type).key
    )


def test_selector_of_things():
    selector_meta = meta_from_dagster_type(Selector({'bar': Field(int)}))
    assert selector_meta.key.startswith('Selector')
    assert selector_meta.kind == ConfigTypeKind.SELECTOR
    assert selector_meta.fields and len(selector_meta.fields) == 1
    field_meta = selector_meta.fields[0]
    assert field_meta.name == 'bar'
    assert field_meta.type_ref.key == 'Int'


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


def test_kitchen_sink_break_out():
    nested_dict_cls = resolve_to_config_type(
        {
            'list_list': [[int]],
            'nested_selector': Selector({'some_field': int, 'list': Noneable([bool])}),
        }
    )
    dict_within_list_cls = resolve_to_config_type(
        {'opt_list_of_int': Field([int], is_required=False), 'nested_dict': Field(nested_dict_cls)}
    )
    kitchen_sink = Array(dict_within_list_cls)

    dict_within_list_key = dict_within_list_cls.key
    kitchen_sink_meta = meta_from_dagster_type(kitchen_sink)

    assert len(kitchen_sink_meta.type_param_refs) == 1
    assert kitchen_sink_meta.type_param_refs[0].key == dict_within_list_key
    assert len(kitchen_sink_meta.inner_type_refs) == 1
    assert kitchen_sink_meta.inner_type_refs[0].key == dict_within_list_key
    dict_within_list_meta = meta_from_dagster_type(dict_within_list_cls)
    assert dict_within_list_meta.type_param_refs is None
    # List[int], Int, Shape.XXX
    assert len(dict_within_list_meta.inner_type_refs) == 3
    assert sorted([type_ref.key for type_ref in dict_within_list_meta.inner_type_refs]) == sorted(
        [nested_dict_cls.key, 'Int', 'Array.Int']
    )
