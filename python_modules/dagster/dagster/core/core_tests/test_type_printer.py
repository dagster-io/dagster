from dagster import types
from dagster.core.type_printer import print_type_to_string


def test_basic_type_print():
    assert print_type_to_string(types.Int) == 'Int'


def test_basic_list_type_print():
    assert print_type_to_string(types.List(types.Int)) == '[Int]'


def test_double_list_type_print():
    assert print_type_to_string(types.List(types.List(types.Int))) == '[[Int]]'


def test_basic_nullable_type_print():
    assert print_type_to_string(types.Nullable(types.Int)) == 'Int?'


def test_nullable_list_combos():
    assert print_type_to_string(types.List(types.Int)) == '[Int]'
    assert print_type_to_string(types.Nullable(types.List(types.Int))) == '[Int]?'
    assert print_type_to_string(types.List(types.Nullable(types.Int))) == '[Int?]'
    assert print_type_to_string(types.Nullable(types.List(types.Nullable(types.Int)))) == '[Int?]?'


def test_basic_dict():
    output = print_type_to_string(types.Dict({'int_field': types.Field(types.Int)}))

    # print('OUTPUT')
    # print(output.replace(' ', '-'))
    # print('******')

    expected = '''{
  int_field: Int
}'''

    assert output == expected


def test_two_field_dicts():
    output = print_type_to_string(
        types.Dict(
            {
                'int_field': types.Field(types.Int),
                'string_field': types.Field(types.String),
            }
        )
    )

    expected = '''{
  int_field: Int
  string_field: String
}'''

    assert output == expected


def test_optional_field():
    output = print_type_to_string(
        types.Dict({
            'int_field': types.Field(types.Int, is_optional=True)
        })
    )

    # print('OUTPUT')
    # print(output.replace(' ', '-'))
    # print('******')

    expected = '''{
  int_field?: Int
}'''

    assert output == expected


def test_single_level_dict_lists_and_nullable():
    output = print_type_to_string(
        types.Dict(
            {
                'nullable_int_field': types.Field(types.Nullable(types.Int)),
                'optional_int_field': types.Field(types.Int, is_optional=True),
                'string_list_field': types.Field(types.List(types.String)),
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
    output = print_type_to_string(
        types.Dict({
            'nested': types.Field(types.Dict({
                'int_field': types.Field(types.Int),
            }))
        })
    )

    expected = '''{
  nested: {
    int_field: Int
  }
}'''

    assert output == expected
