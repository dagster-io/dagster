from six import string_types

from dagster import Dict, Field, PermissiveDict, Selector
from dagster.core.types.field_utils import _compute_fields_hash


def _hash(fields):
    return _compute_fields_hash(fields, description=None, is_system_config=False)


def test_compute_fields_hash():
    assert isinstance(_hash({'some_int': Field(int)}), string_types)


def test_hash_diff():

    assert _hash({'some_int': Field(int)}) != _hash({'another_int': Field(int)})

    assert _hash({'same_name': Field(int)}) != _hash({'same_name': Field(str)})

    assert _hash({'same_name': Field(int)}) != _hash({'same_name': Field(int, is_optional=True)})

    assert _hash({'same_name': Field(int)}) != _hash(
        {'same_name': Field(int, is_optional=True, default_value=2)}
    )

    assert _hash({'same_name': Field(int, is_optional=True)}) != _hash(
        {'same_name': Field(int, is_optional=True, default_value=2)}
    )

    assert _hash({'same_name': Field(int)}) != _hash({'same_name': Field(int, description='desc')})


def test_construct_same_dicts():
    int_dict_1 = Dict(fields={'an_int': Field(int)})
    int_dict_2 = Dict(fields={'an_int': Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.inst().key == int_dict_2.inst().key


def test_field_order_irrelevant():
    int_dict_1 = Dict(fields={'an_int': Field(int), 'another_int': Field(int)})

    int_dict_2 = Dict(fields={'another_int': Field(int), 'an_int': Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.inst().key == int_dict_2.inst().key


def test_construct_different_dicts():
    int_dict = Dict(fields={'an_int': Field(int)})
    string_dict = Dict(fields={'a_string': Field(str)})

    assert int_dict is not string_dict
    assert int_dict.inst().key != string_dict.inst().key


def test_construct_permissive_dict_same_same():
    assert PermissiveDict() is PermissiveDict()


def test_construct_same_perm_dicts():
    int_perm_dict_1 = PermissiveDict(fields={'an_int': Field(int)})
    int_perm_dict_2 = PermissiveDict(fields={'an_int': Field(int)})

    # assert identical object
    assert int_perm_dict_1 is int_perm_dict_2
    # assert equivalent key
    assert int_perm_dict_1.inst().key == int_perm_dict_2.inst().key


def test_construct_different_perm_dicts():
    int_perm_dict = PermissiveDict(fields={'an_int': Field(int)})
    string_perm_dict = PermissiveDict(fields={'a_string': Field(str)})

    assert int_perm_dict is not string_perm_dict
    assert int_perm_dict.inst().key != string_perm_dict.inst().key


def test_construct_same_selectors():
    int_selector_1 = Selector(fields={'an_int': Field(int)})
    int_selector_2 = Selector(fields={'an_int': Field(int)})

    # assert identical object
    assert int_selector_1 is int_selector_2
    # assert equivalent key
    assert int_selector_1.inst().key == int_selector_2.inst().key


def test_construct_different_selectors():
    int_selector = Selector(fields={'an_int': Field(int)})
    string_selector = Selector(fields={'a_string': Field(str)})

    assert int_selector is not string_selector
    assert int_selector.inst().key != string_selector.inst().key


def test_kitchen_sink():
    big_dict_1 = Dict(
        {
            'field_one': Field(int, default_value=2, is_optional=True),
            'field_two': Field(
                Dict(
                    {
                        'nested_field_one': Field(bool),
                        'nested_selector': Field(
                            Selector(
                                {
                                    'int_field_in_selector': Field(int),
                                    'permissive_dict_in_selector': Field(PermissiveDict()),
                                    'permissive_dict_with_fields_in_selector': Field(
                                        PermissiveDict({'string_field': Field(str)})
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )

    big_dict_2 = Dict(
        {
            'field_one': Field(int, default_value=2, is_optional=True),
            'field_two': Field(
                Dict(
                    fields={
                        'nested_field_one': Field(bool),
                        'nested_selector': Field(
                            Selector(
                                fields={
                                    'permissive_dict_in_selector': Field(PermissiveDict()),
                                    'int_field_in_selector': Field(int),
                                    'permissive_dict_with_fields_in_selector': Field(
                                        PermissiveDict(fields={'string_field': Field(str)})
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )

    assert big_dict_1 is big_dict_2
    assert big_dict_1.inst().key == big_dict_2.inst().key

    # differs way down in tree
    big_dict_3 = Dict(
        {
            'field_one': Field(int, default_value=2, is_optional=True),
            'field_two': Field(
                Dict(
                    fields={
                        'nested_field_one': Field(bool),
                        'nested_selector': Field(
                            Selector(
                                fields={
                                    'permissive_dict_in_selector': Field(PermissiveDict()),
                                    'int_field_in_selector': Field(int),
                                    'permissive_dict_with_fields_in_selector': Field(
                                        PermissiveDict(fields={'int_field': Field(int)})
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )

    assert big_dict_1 is not big_dict_3
    assert big_dict_1.inst().key != big_dict_3.inst().key
