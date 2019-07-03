from dagster import PipelineDefinition, SolidDefinition, Int, Field, String, List, Optional, Dict

from dagster.core.types.field import resolve_to_config_type
from dagster.core.types.type_printer import print_type_to_string


def assert_inner_types(parent_type, *dagster_types):
    assert set(list(map(lambda t: t.name, resolve_to_config_type(parent_type).inner_types))) == set(
        map(lambda x: x.name, map(resolve_to_config_type, dagster_types))
    )


def test_basic_type_print():
    assert print_type_to_string(Int) == 'Int'
    assert_inner_types(Int)


def test_basic_list_type_print():
    assert print_type_to_string(List[Int]) == '[Int]'
    assert_inner_types(List[Int], Int)


def test_double_list_type_print():
    assert print_type_to_string(List[List[Int]]) == '[[Int]]'
    int_list = List[Int]
    list_int_list = List[int_list]
    assert_inner_types(list_int_list, Int, int_list)


def test_basic_nullable_type_print():
    assert print_type_to_string(Optional[Int]) == 'Int?'
    nullable_int = Optional[Int]
    assert_inner_types(nullable_int, Int)


def test_nullable_list_combos():
    assert print_type_to_string(List[Int]) == '[Int]'
    assert print_type_to_string(Optional[List[Int]]) == '[Int]?'
    assert print_type_to_string(List[Optional[Int]]) == '[Int?]'
    assert print_type_to_string(Optional[List[Optional[Int]]]) == '[Int?]?'


def test_basic_dict():
    output = print_type_to_string(Dict({'int_field': Field(Int)}))

    expected = '''{
  int_field: Int
}'''

    assert output == expected


def test_two_field_dicts():
    two_field_dict = Dict({'int_field': Field(Int), 'string_field': Field(String)})
    assert_inner_types(two_field_dict, Int, String)

    output = print_type_to_string(two_field_dict)

    expected = '''{
  int_field: Int
  string_field: String
}'''

    assert output == expected


def test_two_field_dicts_same_type():
    two_field_dict = Dict({'int_field1': Field(Int), 'int_field2': Field(Int)})
    assert_inner_types(two_field_dict, Int)

    output = print_type_to_string(two_field_dict)

    expected = '''{
  int_field1: Int
  int_field2: Int
}'''

    assert output == expected


def test_optional_field():
    output = print_type_to_string(Dict({'int_field': Field(Int, is_optional=True)}))

    expected = '''{
  int_field?: Int
}'''

    assert output == expected


def test_single_level_dict_lists_and_nullable():
    output = print_type_to_string(
        Dict(
            {
                'nullable_int_field': Field(Optional[Int]),
                'optional_int_field': Field(Int, is_optional=True),
                'string_list_field': Field(List[String]),
            }
        )
    )

    expected = '''{
  nullable_int_field: Int?
  optional_int_field?: Int
  string_list_field: [String]
}'''

    assert output == expected


def test_nested_dict():
    nested_type = Dict({'int_field': Field(Int)})
    outer_type = Dict({'nested': Field(nested_type)})
    output = print_type_to_string(outer_type)

    assert_inner_types(outer_type, Int, nested_type)

    expected = '''{
  nested: {
    int_field: Int
  }
}'''

    assert output == expected


def test_test_type_pipeline_construction():
    assert define_test_type_pipeline()


def define_solid_for_test_type(name, runtime_type):
    return SolidDefinition(
        name=name,
        input_defs=[],
        output_defs=[],
        config_field=Field(runtime_type),
        compute_fn=lambda _info, _inputs: None,
    )


# launch in dagit with this command:
# dagit -f test_type_printer.py -n define_test_type_pipeline
def define_test_type_pipeline():
    return PipelineDefinition(
        name='test_type_pipeline',
        solid_defs=[
            define_solid_for_test_type('int_config', Int),
            define_solid_for_test_type('list_of_int_config', List[Int]),
            define_solid_for_test_type('nullable_list_of_int_config', Optional[List[Int]]),
            define_solid_for_test_type('list_of_nullable_int_config', List[Optional[Int]]),
            define_solid_for_test_type(
                'nullable_list_of_nullable_int_config', Optional[List[Optional[Int]]]
            ),
            define_solid_for_test_type(
                'simple_dict', Dict({'int_field': Field(Int), 'string_field': Field(String)})
            ),
            define_solid_for_test_type(
                'dict_with_optional_field',
                Dict(
                    {
                        'nullable_int_field': Field(Optional[Int]),
                        'optional_int_field': Field(Int, is_optional=True),
                        'string_list_field': Field(List[String]),
                    }
                ),
            ),
            define_solid_for_test_type(
                'nested_dict', Dict({'nested': Field(Dict({'int_field': Field(Int)}))})
            ),
        ],
    )
