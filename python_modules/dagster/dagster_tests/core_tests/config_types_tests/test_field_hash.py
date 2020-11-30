from dagster import Field, Permissive, Selector, Shape
from dagster.config.field_utils import _compute_fields_hash


def _hash(fields):
    return _compute_fields_hash(fields, description=None)


def test_compute_fields_hash():
    assert isinstance(_hash({"some_int": Field(int)}), str)


def test_hash_diff():

    assert _hash({"some_int": Field(int)}) != _hash({"another_int": Field(int)})

    assert _hash({"same_name": Field(int)}) != _hash({"same_name": Field(str)})

    assert _hash({"same_name": Field(int)}) != _hash({"same_name": Field(int, is_required=False)})

    assert _hash({"same_name": Field(int)}) != _hash(
        {"same_name": Field(int, is_required=False, default_value=2)}
    )

    assert _hash({"same_name": Field(int, is_required=False)}) != _hash(
        {"same_name": Field(int, is_required=False, default_value=2)}
    )

    assert _hash({"same_name": Field(int)}) != _hash({"same_name": Field(int, description="desc")})


def test_construct_same_dicts():
    int_dict_1 = Shape(fields={"an_int": Field(int)})
    int_dict_2 = Shape(fields={"an_int": Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.key == int_dict_2.key


def test_field_order_irrelevant():
    int_dict_1 = Shape(fields={"an_int": Field(int), "another_int": Field(int)})

    int_dict_2 = Shape(fields={"another_int": Field(int), "an_int": Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.key == int_dict_2.key


def test_construct_different_dicts():
    int_dict = Shape(fields={"an_int": Field(int)})
    string_dict = Shape(fields={"a_string": Field(str)})

    assert int_dict is not string_dict
    assert int_dict.key != string_dict.key


def test_construct_permissive_dict_same_same():
    assert Permissive() is Permissive()


def test_construct_same_perm_dicts():
    int_perm_dict_1 = Permissive(fields={"an_int": Field(int)})
    int_perm_dict_2 = Permissive(fields={"an_int": Field(int)})

    # assert identical object
    assert int_perm_dict_1 is int_perm_dict_2
    # assert equivalent key
    assert int_perm_dict_1.key == int_perm_dict_2.key


def test_construct_different_perm_dicts():
    int_perm_dict = Permissive(fields={"an_int": Field(int)})
    string_perm_dict = Permissive(fields={"a_string": Field(str)})

    assert int_perm_dict is not string_perm_dict
    assert int_perm_dict.key != string_perm_dict.key


def test_construct_same_selectors():
    int_selector_1 = Selector(fields={"an_int": Field(int)})
    int_selector_2 = Selector(fields={"an_int": Field(int)})

    # assert identical object
    assert int_selector_1 is int_selector_2
    # assert equivalent key
    assert int_selector_1.key == int_selector_2.key


def test_construct_different_selectors():
    int_selector = Selector(fields={"an_int": Field(int)})
    string_selector = Selector(fields={"a_string": Field(str)})

    assert int_selector is not string_selector
    assert int_selector.key != string_selector.key


def test_kitchen_sink():
    big_dict_1 = Shape(
        {
            "field_one": Field(int, default_value=2, is_required=False),
            "field_two": Field(
                Shape(
                    {
                        "nested_field_one": Field(bool),
                        "nested_selector": Field(
                            Selector(
                                {
                                    "int_field_in_selector": Field(int),
                                    "permissive_dict_in_selector": Field(Permissive()),
                                    "permissive_dict_with_fields_in_selector": Field(
                                        Permissive({"string_field": Field(str)})
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )

    big_dict_2 = Shape(
        {
            "field_one": Field(int, default_value=2, is_required=False),
            "field_two": Field(
                Shape(
                    fields={
                        "nested_field_one": Field(bool),
                        "nested_selector": Field(
                            Selector(
                                fields={
                                    "permissive_dict_in_selector": Field(Permissive()),
                                    "int_field_in_selector": Field(int),
                                    "permissive_dict_with_fields_in_selector": Field(
                                        Permissive(fields={"string_field": Field(str)})
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
    assert big_dict_1.key == big_dict_2.key

    # differs way down in tree
    big_dict_3 = Shape(
        {
            "field_one": Field(int, default_value=2, is_required=False),
            "field_two": Field(
                Shape(
                    fields={
                        "nested_field_one": Field(bool),
                        "nested_selector": Field(
                            Selector(
                                fields={
                                    "permissive_dict_in_selector": Field(Permissive()),
                                    "int_field_in_selector": Field(int),
                                    "permissive_dict_with_fields_in_selector": Field(
                                        Permissive(fields={"int_field": Field(int)})
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
    assert big_dict_1.key != big_dict_3.key
