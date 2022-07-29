from dagster import Field, Int, Map, Noneable, ScalarUnion, String
from dagster._config import (
    config_schema_snapshot_from_config_type,
    get_recursive_type_keys,
    print_config_type_to_string,
    resolve_to_config_type,
    snap_from_config_type,
)
from dagster._legacy import PipelineDefinition, solid


def assert_inner_types(parent_type, *dagster_types):
    config_type = resolve_to_config_type(parent_type)
    config_schema_snapshot = config_schema_snapshot_from_config_type(config_type)

    all_type_keys = get_recursive_type_keys(
        snap_from_config_type(config_type), config_schema_snapshot
    )

    assert set(all_type_keys) == set(
        map(lambda x: x.key, map(resolve_to_config_type, dagster_types))
    )


def test_basic_type_print():
    assert print_config_type_to_string(Int) == "Int"
    assert_inner_types(Int)


def test_basic_list_type_print():
    assert print_config_type_to_string([int]) == "[Int]"
    assert_inner_types([int], Int)


def test_double_list_type_print():
    assert print_config_type_to_string([[int]]) == "[[Int]]"
    int_list = [int]
    list_int_list = [int_list]
    assert_inner_types(list_int_list, Int, int_list)


def test_basic_nullable_type_print():
    assert print_config_type_to_string(Noneable(int)) == "Int?"
    nullable_int = Noneable(int)
    assert_inner_types(nullable_int, Int)


def test_nullable_list_combos():
    assert print_config_type_to_string([int]) == "[Int]"
    assert print_config_type_to_string(Noneable([int])) == "[Int]?"
    assert print_config_type_to_string([Noneable(int)]) == "[Int?]"
    assert print_config_type_to_string(Noneable([Noneable(int)])) == "[Int?]?"


def test_basic_map_type_print():
    assert (
        print_config_type_to_string({str: int})
        == """{
  [String]: Int
}"""
    )
    assert_inner_types({str: int}, int, str)

    assert (
        print_config_type_to_string({int: int})
        == """{
  [Int]: Int
}"""
    )
    assert_inner_types({int: int}, int, int)


def test_map_name_print():
    assert (
        print_config_type_to_string(Map(str, int, key_label_name="name"))
        == """{
  [name: String]: Int
}"""
    )

    assert (
        print_config_type_to_string(Map(int, float, key_label_name="title"))
        == """{
  [title: Int]: Float
}"""
    )


def test_double_map_type_print():
    assert (
        print_config_type_to_string({str: {str: int}})
        == """{
  [String]: {
    [String]: Int
  }
}"""
    )
    int_map = {str: int}
    map_int_map = {str: int_map}
    assert_inner_types(map_int_map, Int, int_map, String)


def test_list_map_nullable_combos():
    # Don't care about newlines here for brevity's sake, those are tested elsewhere
    assert print_config_type_to_string({str: [int]}, with_lines=False) == "{ [String]: [Int] }"
    assert (
        print_config_type_to_string(Noneable({str: [int]}), with_lines=False)
        == "{ [String]: [Int] }?"
    )
    assert (
        print_config_type_to_string({str: Noneable([int])}, with_lines=False)
        == "{ [String]: [Int]? }"
    )
    assert (
        print_config_type_to_string({str: [Noneable(int)]}, with_lines=False)
        == "{ [String]: [Int?] }"
    )
    assert (
        print_config_type_to_string(Noneable({str: [Noneable(int)]}), with_lines=False)
        == "{ [String]: [Int?] }?"
    )
    assert (
        print_config_type_to_string(Noneable({str: Noneable([Noneable(int)])}), with_lines=False)
        == "{ [String]: [Int?]? }?"
    )


def test_basic_dict():
    output = print_config_type_to_string({"int_field": int})

    expected = """{
  int_field: Int
}"""

    assert output == expected


def test_two_field_dicts():
    two_field_dict = {"int_field": int, "string_field": str}
    assert_inner_types(two_field_dict, Int, String)

    output = print_config_type_to_string(two_field_dict)

    expected = """{
  int_field: Int
  string_field: String
}"""

    assert output == expected


def test_two_field_dicts_same_type():
    two_field_dict = {"int_field1": int, "int_field2": int}
    assert_inner_types(two_field_dict, Int)

    output = print_config_type_to_string(two_field_dict)

    expected = """{
  int_field1: Int
  int_field2: Int
}"""

    assert output == expected


def test_optional_field():
    output = print_config_type_to_string({"int_field": Field(int, is_required=False)})

    expected = """{
  int_field?: Int
}"""

    assert output == expected


def test_single_level_dict_lists_maps_and_nullable():
    output = print_config_type_to_string(
        {
            "nullable_int_field": Noneable(int),
            "optional_int_field": Field(int, is_required=False),
            "string_list_field": [str],
            "zmap_list_field": {str: int},
        }
    )

    expected = """{
  nullable_int_field?: Int?
  optional_int_field?: Int
  string_list_field: [String]
  zmap_list_field: {
    [String]: Int
  }
}"""

    assert output == expected


def test_nested_dicts_and_maps():
    output = print_config_type_to_string({"field_one": {str: {"field_two": {str: int}}}})
    expected = """{
  field_one: {
    [String]: {
      field_two: {
        [String]: Int
      }
    }
  }
}"""
    assert output == expected


def test_nested_dict():
    nested_type = {"int_field": int}
    outer_type = {"nested": nested_type}
    output = print_config_type_to_string(outer_type)

    assert_inner_types(outer_type, Int, nested_type)

    expected = """{
  nested: {
    int_field: Int
  }
}"""

    assert output == expected


def test_scalar_union():
    non_scalar_type = {"str_field": String}
    scalar_union_type = ScalarUnion(
        scalar_type=int,
        non_scalar_schema=non_scalar_type,
    )
    assert_inner_types(scalar_union_type, String, Int, non_scalar_type)


def test_test_type_pipeline_construction():
    assert define_test_type_pipeline()


def define_solid_for_test_type(name, config):
    @solid(name=name, config_schema=config, input_defs=[], output_defs=[])
    def a_solid(_):
        return None

    return a_solid


# launch in dagit with this command:
# dagit -f test_type_printer.py -n define_test_type_pipeline
def define_test_type_pipeline():
    return PipelineDefinition(
        name="test_type_pipeline",
        solid_defs=[
            define_solid_for_test_type("int_config", int),
            define_solid_for_test_type("list_of_int_config", [int]),
            define_solid_for_test_type("nullable_list_of_int_config", Noneable([int])),
            define_solid_for_test_type("list_of_nullable_int_config", [Noneable(int)]),
            define_solid_for_test_type(
                "nullable_list_of_nullable_int_config", Noneable([Noneable(int)])
            ),
            define_solid_for_test_type("simple_dict", {"int_field": int, "string_field": str}),
            define_solid_for_test_type(
                "dict_with_optional_field",
                {
                    "nullable_int_field": Noneable(int),
                    "optional_int_field": Field(int, is_required=False),
                    "string_list_field": [str],
                },
            ),
            define_solid_for_test_type("nested_dict", {"nested": {"int_field": int}}),
        ],
    )
