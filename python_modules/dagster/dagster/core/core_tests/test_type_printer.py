from dagster import (
    PipelineDefinition,
    SolidDefinition,
    types,
)

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


def test_test_type_pipeline_construction():
    assert define_test_type_pipeline()


def define_solid_for_test_type(name, dagster_type):
    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[],
        config_field=types.Field(dagster_type),
        transform_fn=lambda _info, _inputs: None,
    )


# launch in dagit with this command:
# dagit -f test_type_printer.py -n define_test_type_pipeline
def define_test_type_pipeline():
    return PipelineDefinition(
        name='test_type_pipeline',
        solids=[
            define_solid_for_test_type('int_config', types.Int),
            define_solid_for_test_type('list_of_int_config', types.List(types.Int)),
            define_solid_for_test_type(
                'nullable_list_of_int_config',
                types.Nullable(types.List(types.Int)),
            ),
            define_solid_for_test_type(
                'list_of_nullable_int_config',
                types.List(types.Nullable(types.Int)),
            ),
            define_solid_for_test_type(
                'nullable_list_of_nullable_int_config',
                types.Nullable(types.List(types.Nullable(types.Int))),
            ),
            define_solid_for_test_type(
                'simple_dict',
                types.Dict(
                    {
                        'int_field': types.Field(types.Int),
                        'string_field': types.Field(types.String),
                    }
                )
            ),
            define_solid_for_test_type(
                'dict_with_optional_field',
                types.Dict(
                    {
                        'nullable_int_field': types.Field(types.Nullable(types.Int)),
                        'optional_int_field': types.Field(types.Int, is_optional=True),
                        'string_list_field': types.Field(types.List(types.String)),
                    }
                ),
            ),
            define_solid_for_test_type(
                'nested_dict',
                types.Dict({
                    'nested': types.Field(types.Dict({
                        'int_field': types.Field(types.Int),
                    }))
                }),
            ),
        ],
    )
