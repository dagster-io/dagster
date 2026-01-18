import dagster as dg
from dagster._config import compute_fields_hash


def _hash(fields):
    return compute_fields_hash(fields, description=None)


def test_compute_fields_hash():
    assert isinstance(_hash({"some_int": dg.Field(int)}), str)


def test_hash_diff():
    assert _hash({"some_int": dg.Field(int)}) != _hash({"another_int": dg.Field(int)})

    assert _hash({"same_name": dg.Field(int)}) != _hash({"same_name": dg.Field(str)})

    assert _hash({"same_name": dg.Field(int)}) != _hash(
        {"same_name": dg.Field(int, is_required=False)}
    )

    assert _hash({"same_name": dg.Field(int)}) != _hash(
        {"same_name": dg.Field(int, is_required=False, default_value=2)}
    )

    assert _hash({"same_name": dg.Field(int, is_required=False)}) != _hash(
        {"same_name": dg.Field(int, is_required=False, default_value=2)}
    )

    assert _hash({"same_name": dg.Field(int)}) != _hash(
        {"same_name": dg.Field(int, description="desc")}
    )


def test_construct_same_dicts():
    int_dict_1 = dg.Shape(fields={"an_int": dg.Field(int)})
    int_dict_2 = dg.Shape(fields={"an_int": dg.Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.key == int_dict_2.key


def test_construct_same_fields_different_aliases():
    int_dict_1 = dg.Shape(fields={"an_int": dg.Field(int)}, field_aliases={"an_int": "foo"})
    int_dict_2 = dg.Shape(fields={"an_int": dg.Field(int)}, field_aliases={"an_int": "bar"})

    assert int_dict_1 is not int_dict_2
    assert not int_dict_1.key == int_dict_2.key


def test_field_order_irrelevant():
    int_dict_1 = dg.Shape(fields={"an_int": dg.Field(int), "another_int": dg.Field(int)})

    int_dict_2 = dg.Shape(fields={"another_int": dg.Field(int), "an_int": dg.Field(int)})

    # assert identical object
    assert int_dict_1 is int_dict_2
    # assert equivalent key
    assert int_dict_1.key == int_dict_2.key


def test_field_alias_order_irrelevant():
    int_dict_1 = dg.Shape(
        fields={"an_int": dg.Field(int), "another_int": dg.Field(int)},
        field_aliases={"an_int": "foo", "another_int": "bar"},
    )
    int_dict_2 = dg.Shape(
        fields={"an_int": dg.Field(int), "another_int": dg.Field(int)},
        field_aliases={"another_int": "bar", "an_int": "foo"},
    )

    assert int_dict_1 is int_dict_2
    assert int_dict_1.key == int_dict_2.key


def test_construct_different_dicts():
    int_dict = dg.Shape(fields={"an_int": dg.Field(int)})
    string_dict = dg.Shape(fields={"a_string": dg.Field(str)})

    assert int_dict is not string_dict
    assert int_dict.key != string_dict.key


def test_construct_permissive_dict_same_same():
    assert dg.Permissive() is dg.Permissive()


def test_construct_same_perm_dicts():
    int_perm_dict_1 = dg.Permissive(fields={"an_int": dg.Field(int)})
    int_perm_dict_2 = dg.Permissive(fields={"an_int": dg.Field(int)})

    # assert identical object
    assert int_perm_dict_1 is int_perm_dict_2
    # assert equivalent key
    assert int_perm_dict_1.key == int_perm_dict_2.key


def test_construct_different_perm_dicts():
    int_perm_dict = dg.Permissive(fields={"an_int": dg.Field(int)})
    string_perm_dict = dg.Permissive(fields={"a_string": dg.Field(str)})

    assert int_perm_dict is not string_perm_dict
    assert int_perm_dict.key != string_perm_dict.key


def test_construct_same_selectors():
    int_selector_1 = dg.Selector(fields={"an_int": dg.Field(int)})
    int_selector_2 = dg.Selector(fields={"an_int": dg.Field(int)})

    # assert identical object
    assert int_selector_1 is int_selector_2
    # assert equivalent key
    assert int_selector_1.key == int_selector_2.key


def test_construct_different_selectors():
    int_selector = dg.Selector(fields={"an_int": dg.Field(int)})
    string_selector = dg.Selector(fields={"a_string": dg.Field(str)})

    assert int_selector is not string_selector
    assert int_selector.key != string_selector.key


def test_kitchen_sink():
    big_dict_1 = dg.Shape(
        {
            "field_one": dg.Field(int, default_value=2, is_required=False),
            "field_two": dg.Field(
                dg.Shape(
                    {
                        "nested_field_one": dg.Field(bool),
                        "nested_selector": dg.Field(
                            dg.Selector(
                                {
                                    "int_field_in_selector": dg.Field(int),
                                    "permissive_dict_in_selector": dg.Field(dg.Permissive()),
                                    "permissive_dict_with_fields_in_selector": dg.Field(
                                        dg.Permissive({"string_field": dg.Field(str)})
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )

    big_dict_2 = dg.Shape(
        {
            "field_one": dg.Field(int, default_value=2, is_required=False),
            "field_two": dg.Field(
                dg.Shape(
                    fields={
                        "nested_field_one": dg.Field(bool),
                        "nested_selector": dg.Field(
                            dg.Selector(
                                fields={
                                    "permissive_dict_in_selector": dg.Field(dg.Permissive()),
                                    "int_field_in_selector": dg.Field(int),
                                    "permissive_dict_with_fields_in_selector": dg.Field(
                                        dg.Permissive(fields={"string_field": dg.Field(str)})
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
    big_dict_3 = dg.Shape(
        {
            "field_one": dg.Field(int, default_value=2, is_required=False),
            "field_two": dg.Field(
                dg.Shape(
                    fields={
                        "nested_field_one": dg.Field(bool),
                        "nested_selector": dg.Field(
                            dg.Selector(
                                fields={
                                    "permissive_dict_in_selector": dg.Field(dg.Permissive()),
                                    "int_field_in_selector": dg.Field(int),
                                    "permissive_dict_with_fields_in_selector": dg.Field(
                                        dg.Permissive(fields={"int_field": dg.Field(int)})
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
