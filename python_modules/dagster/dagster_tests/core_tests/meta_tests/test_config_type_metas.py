from dagster import Dict, Field, List, Optional, Selector, Set, Tuple
from dagster.core.meta.config_types import (
    ConfigTypeKind,
    ConfigTypeMeta,
    NonGenericTypeRefMeta,
    meta_from_config_type,
)
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.core.types.field import resolve_to_config_type


def meta_from_dagster_type(dagster_type):
    return meta_from_config_type(resolve_to_config_type(dagster_type))


def test_basic_int_meta():
    int_meta = meta_from_dagster_type(int)
    assert int_meta.name == 'Int'
    assert int_meta.key == 'Int'
    assert int_meta.kind == ConfigTypeKind.SCALAR
    assert int_meta.inner_type_refs == []
    assert int_meta.is_builtin is True
    assert int_meta.is_system_config is False
    assert int_meta.enum_values is None
    assert int_meta.fields is None


def test_basic_dict():
    dict_meta = meta_from_dagster_type(Dict({'foo': Field(int)}))
    assert dict_meta.key.startswith('Dict.')
    assert dict_meta.name is None
    assert dict_meta.inner_type_refs
    assert len(dict_meta.inner_type_refs) == 1
    assert dict_meta.inner_type_refs[0].key == 'Int'
    assert dict_meta.is_builtin is True
    assert dict_meta.is_system_config is False
    assert dict_meta.enum_values is None

    assert dict_meta.fields and len(dict_meta.fields) == 1

    field = dict_meta.fields[0]
    assert field.name == 'foo'


def test_field_things():
    dict_meta = meta_from_dagster_type(
        Dict(
            {
                'req': Field(int),
                'opt': Field(int, is_optional=True),
                'opt_with_default': Field(int, is_optional=True, default_value=2),
                'req_with_desc': Field(int, description='A desc'),
            }
        )
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
    list_meta = meta_from_dagster_type(List[int])
    assert list_meta.key.startswith('List')
    assert list_meta.inner_type_refs
    assert len(list_meta.inner_type_refs) == 1
    assert list_meta.inner_type_refs[0].key == 'Int'
    assert list_meta.is_builtin is True
    assert list_meta.is_system_config is False
    assert list_meta.enum_values is None


def test_basic_optional():
    optional_meta = meta_from_dagster_type(Optional[int])
    assert optional_meta.key.startswith('Optional')
    assert optional_meta.inner_type_refs
    assert len(optional_meta.inner_type_refs) == 1
    assert optional_meta.inner_type_refs[0].key == 'Int'
    # https://github.com/dagster-io/dagster/issues/1933
    # TODO reconcile names
    assert optional_meta.kind == ConfigTypeKind.NULLABLE
    assert optional_meta.is_builtin is True
    assert optional_meta.is_system_config is False
    assert optional_meta.enum_values is None


def test_basic_list_list():
    list_meta = meta_from_dagster_type(List[List[int]])
    assert list_meta.key.startswith('List')
    assert list_meta.inner_type_refs
    assert len(list_meta.inner_type_refs) == 2
    refs = {ref.key: ref for ref in list_meta.inner_type_refs}
    assert (
        len(refs['List.Int'].inner_type_refs) == 1
        and isinstance(refs['List.Int'], ConfigTypeMeta)
        and refs['List.Int'].inner_type_refs[0].key == 'Int'
    )
    assert refs['Int'].key == 'Int'
    assert list_meta.is_builtin is True
    assert list_meta.is_system_config is False
    assert list_meta.enum_values is None

    assert (
        len(list_meta.type_param_refs) == 1
        and list_meta.type_param_refs[0].kind == ConfigTypeKind.LIST
    )


def test_list_of_dict():
    inner_dict_dagster_type = Dict({'foo': Field(str)})
    list_of_dict_meta = meta_from_dagster_type(List[inner_dict_dagster_type])

    assert list_of_dict_meta.key.startswith('List')
    assert list_of_dict_meta.inner_type_refs
    assert len(list_of_dict_meta.inner_type_refs) == 1
    # Both Dict[...] and str are NonGenericTypeRefMetas in this schema
    dict_ref = list_of_dict_meta.type_param_refs[0]
    assert isinstance(dict_ref, NonGenericTypeRefMeta)
    assert dict_ref.key.startswith('Dict')

    assert (
        len(list_of_dict_meta.type_param_refs) == 1
        and list_of_dict_meta.type_param_refs[0].key
        == resolve_to_config_type(inner_dict_dagster_type).key
    )


def test_tuple_of_things():
    tuple_meta = meta_from_dagster_type(Tuple[bool, str, List[int]])
    assert tuple_meta.key.startswith('Tuple')
    assert len(tuple_meta.type_param_refs) == 3
    assert [ref.key for ref in tuple_meta.type_param_refs] == ['Bool', 'String', 'List.Int']

    assert len(tuple_meta.inner_type_refs) == 4


def test_set_of_things():
    tuple_meta = meta_from_dagster_type(Set[Tuple[int, str, List[int]]])
    assert tuple_meta.key.startswith('Set')
    assert len(tuple_meta.type_param_refs) == 1
    print([type_ref.key for type_ref in tuple_meta.inner_type_refs])
    assert len(tuple_meta.inner_type_refs) == 4


def test_selector_of_things():
    selector_meta = meta_from_dagster_type(Selector({'bar': Field(int)}))
    assert selector_meta.key.startswith('Selector')
    assert selector_meta.kind == ConfigTypeKind.SELECTOR
    assert selector_meta.fields and len(selector_meta.fields) == 1
    field_meta = selector_meta.fields[0]
    assert field_meta.name == 'bar'
    assert field_meta.type_ref.key == 'Int'


def test_kitchen_sink():
    kitchen_sink = List[
        Dict(
            {
                'opt_list_of_int': Field(List[int], is_optional=True),
                'tuple_of_things': Field(Tuple[int, str]),
                'nested_dict': Field(
                    Dict(
                        {
                            'list_list': Field(List[List[int]]),
                            'nested_selector': Field(
                                Selector(
                                    {'some_field': Field(int), 'set': Field(Optional[Set[bool]])}
                                )
                            ),
                        }
                    )
                ),
            }
        )
    ]

    kitchen_sink_meta = meta_from_dagster_type(kitchen_sink)

    rehydrated_meta = deserialize_json_to_dagster_namedtuple(
        serialize_dagster_namedtuple(kitchen_sink_meta)
    )
    assert kitchen_sink_meta == rehydrated_meta


def test_kitchen_sink_break_out():
    nested_dict_cls = Dict(
        {
            'list_list': Field(List[List[int]]),
            'nested_selector': Field(
                Selector({'some_field': Field(int), 'set': Field(Optional[Set[bool]])})
            ),
        }
    )
    dict_within_list_cls = Dict(
        {
            'opt_list_of_int': Field(List[int], is_optional=True),
            'tuple_of_things': Field(Tuple[int, str]),
            'nested_dict': Field(nested_dict_cls),
        }
    )
    kitchen_sink = List[dict_within_list_cls]

    dict_within_list_key = dict_within_list_cls.inst().key
    kitchen_sink_meta = meta_from_dagster_type(kitchen_sink)

    assert len(kitchen_sink_meta.type_param_refs) == 1
    assert kitchen_sink_meta.type_param_refs[0].key == dict_within_list_key
    assert len(kitchen_sink_meta.inner_type_refs) == 1
    assert kitchen_sink_meta.inner_type_refs[0].key == dict_within_list_key
    dict_within_list_meta = meta_from_dagster_type(dict_within_list_cls)
    assert dict_within_list_meta.type_param_refs is None
    # List[int], Int, Tuple[int, str], str, Dict.XXX
    assert len(dict_within_list_meta.inner_type_refs) == 5
    assert sorted([type_ref.key for type_ref in dict_within_list_meta.inner_type_refs]) == sorted(
        [
            nested_dict_cls.inst().key,
            'Int',
            'List.Int',
            meta_from_dagster_type(Tuple[int, str]).key,
            'String',
        ]
    )
