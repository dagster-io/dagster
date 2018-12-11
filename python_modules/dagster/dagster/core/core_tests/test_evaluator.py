from dagster import types

from dagster.core.evaluator import (
    DagsterEvaluationErrorReason,
    EvaluationStackListItemEntry,
    EvaluationStackPathEntry,
    EvaluateValueResult,
    evaluate_config_value,
)


def assert_success(result, expected_value):
    assert result.success
    assert result.value == expected_value


def test_evaluate_scalar_success():
    assert_success(evaluate_config_value(types.String, 'foobar'), 'foobar')
    assert_success(evaluate_config_value(types.Int, 34234), 34234)
    assert_success(evaluate_config_value(types.Bool, True), True)


def test_evaluate_scalar_failure():
    result = evaluate_config_value(types.String, 2343)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries
    assert error.error_data.dagster_type.name == 'String'
    assert error.error_data.value_rep == '2343'


SingleLevelDict = types.Dict({
    'level_one': types.Field(types.String),
}, )


def test_single_error():
    success_value = {'level_one': 'ksjdfd'}
    assert_success(evaluate_config_value(SingleLevelDict, success_value), success_value)


def test_single_level_scalar_mismatch():
    value = {'level_one': 234}
    result = evaluate_config_value(SingleLevelDict, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 1
    assert error.stack.entries[0].field_name == 'level_one'
    assert error.stack.entries[0].field_def.dagster_type.name == 'String'


def test_single_level_dict_not_a_dict():
    value = 'not_a_dict'
    result = evaluate_config_value(SingleLevelDict, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries


def test_root_missing_field():
    result = evaluate_config_value(SingleLevelDict, {})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert len(result.errors_at_level()) == 1
    assert error.error_data.field_name == 'level_one'


DoubleLevelDict = types.Dict(
    {
        'level_one':
        types.Field(
            types.Dict(
                {
                    'string_field': types.Field(types.String),
                    'int_field': types.Field(types.Int, is_optional=True, default_value=989),
                    'bool_field': types.Field(types.Bool),
                },
            ),
        ),
    },
)


def test_nested_success():
    value = {
        'level_one': {
            'string_field': 'skdsjfkdj',
            'int_field': 123,
            'bool_field': True,
        }
    }

    assert_success(evaluate_config_value(DoubleLevelDict, value), value)

    result = evaluate_config_value(
        DoubleLevelDict,
        {
            'level_one': {
                'string_field': 'kjfkd',
                'bool_field': True,
            },
        },
    )

    assert isinstance(result, EvaluateValueResult)

    assert result.success
    assert result.value['level_one']['int_field'] == 989


def test_nested_error_one_field_not_defined():
    value = {
        'level_one': {
            'string_field': 'skdsjfkdj',
            'int_field': 123,
            'bool_field': True,
            'no_field_one': 'kdjfkd',
        }
    }

    result = evaluate_config_value(DoubleLevelDict, value)

    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert error.error_data.field_name == 'no_field_one'
    assert len(error.stack.entries) == 1
    stack_entry = error.stack.entries[0]
    assert stack_entry.field_name == 'level_one'
    assert 'Dict' in stack_entry.field_def.dagster_type.name


def get_field_name_error(result, field_name):
    for error in result.errors:
        if error.error_data.field_name == field_name:
            return error
    assert False


def test_nested_error_two_fields_not_defined():
    value = {
        'level_one': {
            'string_field': 'skdsjfkdj',
            'int_field': 123,
            'bool_field': True,
            'no_field_one': 'kdjfkd',
            'no_field_two': 'kdjfkd',
        }
    }

    result = evaluate_config_value(DoubleLevelDict, value)

    assert not result.success
    assert len(result.errors) == 2

    field_one_error = get_field_name_error(result, 'no_field_one')
    field_two_error = get_field_name_error(result, 'no_field_two')

    assert field_one_error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert field_one_error.error_data.field_name == 'no_field_one'
    assert field_two_error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert field_two_error.error_data.field_name == 'no_field_two'


def test_nested_error_missing_fields():
    value = {
        'level_one': {
            'string_field': 'skdsjfkdj',
        }
    }

    result = evaluate_config_value(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert error.error_data.field_name == 'bool_field'


def test_nested_error_multiple_missing_fields():
    value = {'level_one': {}}

    result = evaluate_config_value(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 2

    assert get_field_name_error(
        result,
        'bool_field',
    ).reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert get_field_name_error(
        result,
        'string_field',
    ).reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD


def test_nested_missing_and_not_defined():
    value = {'level_one': {'not_defined': 'kjdfkdj'}}

    result = evaluate_config_value(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 3

    assert get_field_name_error(
        result,
        'bool_field',
    ).reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD

    assert get_field_name_error(
        result,
        'string_field',
    ).reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD

    assert get_field_name_error(
        result,
        'not_defined',
    ).reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED


MultiLevelDictType = types.Dict(
    {
        'level_one_string_field':
        types.Field(types.String),
        'level_two_dict':
        types.Field(
            types.Dict(
                {
                    'level_two_int_field':
                    types.Field(types.Int),
                    'level_three_dict':
                    types.Field(types.Dict({
                        'level_three_string': types.Field(types.String),
                    })),
                }
            )
        ),
    },
)


def test_multilevel_success():
    working_value = {
        'level_one_string_field': 'foo',
        'level_two_dict': {
            'level_two_int_field': 234234,
            'level_three_dict': {
                'level_three_string': 'kjdfkd',
            },
        },
    }

    assert_success(evaluate_config_value(MultiLevelDictType, working_value), working_value)


def test_deep_scalar():
    value = {
        'level_one_string_field': 'foo',
        'level_two_dict': {
            'level_two_int_field': 234234,
            'level_three_dict': {
                'level_three_string': 123,
            },
        },
    }

    result = evaluate_config_value(MultiLevelDictType, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert error.error_data.dagster_type.name == 'String'
    assert error.error_data.value_rep == '123'
    assert len(error.stack.entries) == 3

    assert [entry.field_name for entry in error.stack.entries] == [
        'level_two_dict',
        'level_three_dict',
        'level_three_string',
    ]

    assert not result.errors_at_level('level_one_string_field')
    assert not result.errors_at_level('level_two_dict')
    assert not result.errors_at_level('level_two_dict', 'level_three_dict')
    assert len(
        result.errors_at_level(
            'level_two_dict',
            'level_three_dict',
            'level_three_string',
        ),
    ) == 1


def test_deep_mixed_level_errors():
    value = {
        'level_one_string_field': 'foo',
        'level_one_not_defined': 'kjsdkfjd',
        'level_two_dict': {
            # 'level_two_int_field': 234234, # missing
            'level_three_dict': {
                'level_three_string': 123,
            },
        },
    }

    result = evaluate_config_value(MultiLevelDictType, value)
    assert not result.success
    assert len(result.errors) == 3

    root_errors = result.errors_at_level()
    assert len(root_errors) == 1
    root_error = root_errors[0]
    assert root_error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert root_error.error_data.field_name == 'level_one_not_defined'

    level_two_errors = result.errors_at_level('level_two_dict')
    assert len(level_two_errors) == 1
    level_two_error = level_two_errors[0]
    assert level_two_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert level_two_error.error_data.field_name == 'level_two_int_field'

    assert not result.errors_at_level('level_two_dict', 'level_three_dict')

    final_level_errors = result.errors_at_level(
        'level_two_dict',
        'level_three_dict',
        'level_three_string',
    )

    assert len(final_level_errors) == 1
    final_level_error = final_level_errors[0]

    assert final_level_error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


class ExampleSelectorType(types.DagsterSelectorType):
    def __init__(self):
        super(ExampleSelectorType, self).__init__(
            'ExampleSelector',
            fields={
                'option_one': types.Field(types.String),
                'option_two': types.Field(types.String),
            }
        )


ExampleSelector = ExampleSelectorType()


def test_example_selector_success():
    result = evaluate_config_value(ExampleSelector, {'option_one': 'foo'})
    assert result.success
    assert result.value == {'option_one': 'foo'}

    result = evaluate_config_value(ExampleSelector, {'option_two': 'foo'})
    assert result.success
    assert result.value == {'option_two': 'foo'}


def test_example_selector_error_top_level_type():
    result = evaluate_config_value(ExampleSelector, 'kjsdkf')
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_example_selector_wrong_field():
    result = evaluate_config_value(ExampleSelector, {'nope': 234})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED


def test_example_selector_multiple_fields():
    result = evaluate_config_value(ExampleSelector, {
        'option_one': 'foo',
        'option_two': 'boo',
    })

    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR


class SelectorWithDefaultsType(types.DagsterSelectorType):
    def __init__(self):
        super(SelectorWithDefaultsType, self).__init__(
            'SelectorWithDefaultsType',
            {'default': types.Field(types.String, is_optional=True, default_value='foo')}
        )


SelectorWithDefaults = SelectorWithDefaultsType()


def test_selector_with_defaults():
    result = evaluate_config_value(SelectorWithDefaults, {})
    assert result.success
    assert result.value == {'default': 'foo'}


def test_evaluate_list_string():
    string_list = types.List(types.String)
    result = evaluate_config_value(string_list, ["foo"])
    assert result.success
    assert result.value == ["foo"]


def test_evaluate_list_error_item_mismatch():
    string_list = types.List(types.String)
    result = evaluate_config_value(string_list, [1])
    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_evaluate_list_error_top_level_mismatch():
    string_list = types.List(types.String)
    result = evaluate_config_value(string_list, 1)
    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_evaluate_double_list():
    string_double_list = types.List(types.List(types.String))
    result = evaluate_config_value(string_double_list, [['foo']])
    assert result.success
    assert result.value == [['foo']]


def test_config_list_in_dict():
    nested_list = types.Dict({
        'nested_list': types.Field(types.List(types.Int)),
    }, )

    value = {'nested_list': [1, 2, 3]}
    result = evaluate_config_value(nested_list, value)
    assert result.success
    assert result.value == value


def test_config_list_in_dict_error():
    nested_list = types.Dict({
        'nested_list': types.Field(types.List(types.Int)),
    }, )

    value = {'nested_list': [1, 'bar', 3]}
    result = evaluate_config_value(nested_list, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 2
    stack_entry = error.stack.entries[0]
    assert isinstance(stack_entry, EvaluationStackPathEntry)
    assert stack_entry.field_name == 'nested_list'
    assert stack_entry.field_def.dagster_type.name == 'List.Int'
    list_entry = error.stack.entries[1]
    assert isinstance(list_entry, EvaluationStackListItemEntry)
    assert list_entry.list_index == 1


def test_config_double_list():
    nested_lists = types.Dict(
        {
            'nested_list_one': types.Field(types.List(types.Int)),
            'nested_list_two': types.Field(types.List(types.String)),
        },
    )

    value = {'nested_list_one': [1, 2, 3], 'nested_list_two': ['foo', 'bar']}

    result = evaluate_config_value(nested_lists, value)
    assert result.success
    assert result.value == value

    error_value = {'nested_list_one': 'kjdfkdj', 'nested_list_two': ['bar']}

    error_result = evaluate_config_value(nested_lists, error_value)
    assert not error_result.success


def test_config_double_list_double_error():
    nested_lists = types.Dict(
        fields={
            'nested_list_one': types.Field(types.List(types.Int)),
            'nested_list_two': types.Field(types.List(types.String)),
        },
    )

    error_value = {'nested_list_one': 'kjdfkdj', 'nested_list_two': ['bar', 2]}
    error_result = evaluate_config_value(nested_lists, error_value)
    assert not error_result.success
    assert len(error_result.errors) == 2


def test_nullable_int():
    assert not evaluate_config_value(types.Int, None).success
    assert evaluate_config_value(types.Int, 0).success
    assert evaluate_config_value(types.Int, 1).success

    assert evaluate_config_value(types.Nullable(types.Int), None).success
    assert evaluate_config_value(types.Nullable(types.Int), 0).success
    assert evaluate_config_value(types.Nullable(types.Int), 1).success


def test_nullable_list():
    list_of_ints = types.List(types.Int)

    assert not evaluate_config_value(list_of_ints, None).success
    assert evaluate_config_value(list_of_ints, []).success
    assert not evaluate_config_value(list_of_ints, [None]).success
    assert evaluate_config_value(list_of_ints, [1]).success

    nullable_list_of_ints = types.Nullable(types.List(types.Int))

    assert evaluate_config_value(nullable_list_of_ints, None).success
    assert evaluate_config_value(nullable_list_of_ints, []).success
    assert not evaluate_config_value(nullable_list_of_ints, [None]).success
    assert evaluate_config_value(nullable_list_of_ints, [1]).success

    list_of_nullable_ints = types.List(types.Nullable(types.Int))

    assert not evaluate_config_value(list_of_nullable_ints, None).success
    assert evaluate_config_value(list_of_nullable_ints, []).success
    assert evaluate_config_value(list_of_nullable_ints, [None]).success
    assert evaluate_config_value(list_of_nullable_ints, [1]).success

    nullable_list_of_nullable_ints = types.Nullable(types.List(types.Nullable(types.Int)))

    assert evaluate_config_value(nullable_list_of_nullable_ints, None).success
    assert evaluate_config_value(nullable_list_of_nullable_ints, []).success
    assert evaluate_config_value(nullable_list_of_nullable_ints, [None]).success
    assert evaluate_config_value(nullable_list_of_nullable_ints, [1]).success


def test_nullable_dict():
    dict_with_int = types.Dict({'int_field': types.Field(types.Int)})

    assert not evaluate_config_value(dict_with_int, None).success
    assert not evaluate_config_value(dict_with_int, {}).success
    assert not evaluate_config_value(dict_with_int, {'int_field': None}).success
    assert evaluate_config_value(dict_with_int, {'int_field': 1}).success

    nullable_dict_with_int = types.Nullable(types.Dict({'int_field': types.Field(types.Int)}))

    assert evaluate_config_value(nullable_dict_with_int, None).success
    assert not evaluate_config_value(nullable_dict_with_int, {}).success
    assert not evaluate_config_value(nullable_dict_with_int, {'int_field': None}).success
    assert evaluate_config_value(nullable_dict_with_int, {'int_field': 1}).success

    dict_with_nullable_int = types.Dict({
        'int_field': types.Field(types.Nullable(types.Int)),
    })

    assert not evaluate_config_value(dict_with_nullable_int, None).success
    assert not evaluate_config_value(dict_with_nullable_int, {}).success
    assert evaluate_config_value(dict_with_nullable_int, {'int_field': None}).success
    assert evaluate_config_value(dict_with_nullable_int, {'int_field': 1}).success

    nullable_dict_with_nullable_int = types.Nullable(
        types.Dict({
            'int_field': types.Field(types.Nullable(types.Int)),
        })
    )

    assert evaluate_config_value(nullable_dict_with_nullable_int, None).success
    assert not evaluate_config_value(nullable_dict_with_nullable_int, {}).success
    assert evaluate_config_value(nullable_dict_with_nullable_int, {'int_field': None}).success
    assert evaluate_config_value(nullable_dict_with_nullable_int, {'int_field': 1}).success
