from dagster import Field, Dict, String, Int, Bool, Nullable, List, Selector, Any

from dagster.core.types.evaluator import (
    DagsterEvaluationErrorReason,
    EvaluationStackListItemEntry,
    EvaluationStackPathEntry,
    EvaluateValueResult,
    evaluate_config_value,
)
from dagster.core.types.field import resolve_to_config_type


def eval_config_value_from_dagster_type(dagster_type, value):
    return evaluate_config_value(resolve_to_config_type(dagster_type), value)


def assert_success(result, expected_value):
    assert result.success
    assert result.value == expected_value


def test_evaluate_scalar_success():
    assert_success(eval_config_value_from_dagster_type(String, 'foobar'), 'foobar')
    assert_success(eval_config_value_from_dagster_type(Int, 34234), 34234)
    assert_success(eval_config_value_from_dagster_type(Bool, True), True)


def test_evaluate_scalar_failure():
    result = eval_config_value_from_dagster_type(String, 2343)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries
    assert error.error_data.config_type.name == 'String'
    assert error.error_data.value_rep == '2343'


SingleLevelDict = Dict({'level_one': Field(String)})


def test_single_error():
    success_value = {'level_one': 'ksjdfd'}
    assert_success(
        eval_config_value_from_dagster_type(SingleLevelDict, success_value), success_value
    )


def test_single_level_scalar_mismatch():
    value = {'level_one': 234}
    result = eval_config_value_from_dagster_type(SingleLevelDict, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 1
    assert error.stack.entries[0].field_name == 'level_one'
    assert error.stack.entries[0].field_def.config_type.name == 'String'


def test_single_level_dict_not_a_dict():
    value = 'not_a_dict'
    result = eval_config_value_from_dagster_type(SingleLevelDict, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries


def test_root_missing_field():
    result = eval_config_value_from_dagster_type(SingleLevelDict, {})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert len(result.errors_at_level()) == 1
    assert error.error_data.field_name == 'level_one'


DoubleLevelDict = Dict(
    {
        'level_one': Field(
            Dict(
                {
                    'string_field': Field(String),
                    'int_field': Field(Int, is_optional=True, default_value=989),
                    'bool_field': Field(Bool),
                }
            )
        )
    }
)


def test_nested_success():
    value = {'level_one': {'string_field': 'skdsjfkdj', 'int_field': 123, 'bool_field': True}}

    assert_success(eval_config_value_from_dagster_type(DoubleLevelDict, value), value)

    result = eval_config_value_from_dagster_type(
        DoubleLevelDict, {'level_one': {'string_field': 'kjfkd', 'bool_field': True}}
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

    result = eval_config_value_from_dagster_type(DoubleLevelDict, value)

    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert error.error_data.field_name == 'no_field_one'
    assert len(error.stack.entries) == 1
    stack_entry = error.stack.entries[0]
    assert stack_entry.field_name == 'level_one'
    assert 'Dict' in stack_entry.field_def.config_type.key


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

    result = eval_config_value_from_dagster_type(DoubleLevelDict, value)

    assert not result.success
    assert len(result.errors) == 1

    fields_error = result.errors[0]

    assert fields_error.reason == DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED

    assert fields_error.error_data.field_names == ['no_field_one', 'no_field_two']


def test_nested_error_missing_fields():
    value = {'level_one': {'string_field': 'skdsjfkdj'}}

    result = eval_config_value_from_dagster_type(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert error.error_data.field_name == 'bool_field'


def test_nested_error_multiple_missing_fields():
    value = {'level_one': {}}

    result = eval_config_value_from_dagster_type(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 1

    fields_error = result.errors[0]
    assert fields_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    assert fields_error.error_data.field_names == ['bool_field', 'string_field']


def test_nested_missing_and_not_defined():
    value = {'level_one': {'not_defined': 'kjdfkdj'}}

    result = eval_config_value_from_dagster_type(DoubleLevelDict, value)
    assert not result.success
    assert len(result.errors) == 2

    fields_error = [
        error
        for error in result.errors
        if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    ][0]

    assert fields_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    assert fields_error.error_data.field_names == ['bool_field', 'string_field']

    assert (
        get_field_name_error(result, 'not_defined').reason
        == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    )


MultiLevelDictType = Dict(
    {
        'level_one_string_field': Field(String),
        'level_two_dict': Field(
            Dict(
                {
                    'level_two_int_field': Field(Int),
                    'level_three_dict': Field(Dict({'level_three_string': Field(String)})),
                }
            )
        ),
    }
)


def test_multilevel_success():
    working_value = {
        'level_one_string_field': 'foo',
        'level_two_dict': {
            'level_two_int_field': 234234,
            'level_three_dict': {'level_three_string': 'kjdfkd'},
        },
    }

    assert_success(
        eval_config_value_from_dagster_type(MultiLevelDictType, working_value), working_value
    )


def test_deep_scalar():
    value = {
        'level_one_string_field': 'foo',
        'level_two_dict': {
            'level_two_int_field': 234234,
            'level_three_dict': {'level_three_string': 123},
        },
    }

    result = eval_config_value_from_dagster_type(MultiLevelDictType, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert error.error_data.config_type.name == 'String'
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
    assert (
        len(result.errors_at_level('level_two_dict', 'level_three_dict', 'level_three_string')) == 1
    )


def test_deep_mixed_level_errors():
    value = {
        'level_one_string_field': 'foo',
        'level_one_not_defined': 'kjsdkfjd',
        'level_two_dict': {
            # 'level_two_int_field': 234234, # missing
            'level_three_dict': {'level_three_string': 123}
        },
    }

    result = eval_config_value_from_dagster_type(MultiLevelDictType, value)
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
        'level_two_dict', 'level_three_dict', 'level_three_string'
    )

    assert len(final_level_errors) == 1
    final_level_error = final_level_errors[0]

    assert final_level_error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


ExampleSelector = Selector({'option_one': Field(String), 'option_two': Field(String)})


def test_example_selector_success():
    result = eval_config_value_from_dagster_type(ExampleSelector, {'option_one': 'foo'})
    assert result.success
    assert result.value == {'option_one': 'foo'}

    result = eval_config_value_from_dagster_type(ExampleSelector, {'option_two': 'foo'})
    assert result.success
    assert result.value == {'option_two': 'foo'}


def test_example_selector_error_top_level_type():
    result = eval_config_value_from_dagster_type(ExampleSelector, 'kjsdkf')
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_example_selector_wrong_field():
    result = eval_config_value_from_dagster_type(ExampleSelector, {'nope': 234})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED


def test_example_selector_multiple_fields():
    result = eval_config_value_from_dagster_type(
        ExampleSelector, {'option_one': 'foo', 'option_two': 'boo'}
    )

    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR


def test_selector_within_dict_no_subfields():
    result = eval_config_value_from_dagster_type(
        Dict({'selector': Field(ExampleSelector)}), {'selector': {}}
    )
    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].message == (
        "Must specify a field at path root:selector if more than one field "
        "is defined. Defined fields: ['option_one', 'option_two']"
    )


SelectorWithDefaults = Selector({'default': Field(String, is_optional=True, default_value='foo')})


def test_selector_with_defaults():
    result = eval_config_value_from_dagster_type(SelectorWithDefaults, {})
    assert result.success
    assert result.value == {'default': 'foo'}


def test_evaluate_list_string():
    string_list = List(String)
    result = eval_config_value_from_dagster_type(string_list, ["foo"])
    assert result.success
    assert result.value == ["foo"]


def test_evaluate_list_error_item_mismatch():
    string_list = List(String)
    result = eval_config_value_from_dagster_type(string_list, [1])
    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_evaluate_list_error_top_level_mismatch():
    string_list = List(String)
    result = eval_config_value_from_dagster_type(string_list, 1)
    assert not result.success
    assert len(result.errors) == 1
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_evaluate_double_list():
    string_double_list = List(List(String))
    result = eval_config_value_from_dagster_type(string_double_list, [['foo']])
    assert result.success
    assert result.value == [['foo']]


def test_config_list_in_dict():
    nested_list = Dict({'nested_list': Field(List(Int))})

    value = {'nested_list': [1, 2, 3]}
    result = eval_config_value_from_dagster_type(nested_list, value)
    assert result.success
    assert result.value == value


def test_config_list_in_dict_error():
    nested_list = Dict({'nested_list': Field(List(Int))})

    value = {'nested_list': [1, 'bar', 3]}
    result = eval_config_value_from_dagster_type(nested_list, value)
    assert not result.success
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 2
    stack_entry = error.stack.entries[0]
    assert isinstance(stack_entry, EvaluationStackPathEntry)
    assert stack_entry.field_name == 'nested_list'
    list_entry = error.stack.entries[1]
    assert isinstance(list_entry, EvaluationStackListItemEntry)
    assert list_entry.list_index == 1


def test_config_double_list():
    nested_lists = Dict(
        {'nested_list_one': Field(List(Int)), 'nested_list_two': Field(List(String))}
    )

    value = {'nested_list_one': [1, 2, 3], 'nested_list_two': ['foo', 'bar']}

    result = eval_config_value_from_dagster_type(nested_lists, value)
    assert result.success
    assert result.value == value

    error_value = {'nested_list_one': 'kjdfkdj', 'nested_list_two': ['bar']}

    error_result = eval_config_value_from_dagster_type(nested_lists, error_value)
    assert not error_result.success


def test_config_double_list_double_error():
    nested_lists = Dict(
        fields={'nested_list_one': Field(List(Int)), 'nested_list_two': Field(List(String))}
    )

    error_value = {'nested_list_one': 'kjdfkdj', 'nested_list_two': ['bar', 2]}
    error_result = eval_config_value_from_dagster_type(nested_lists, error_value)
    assert not error_result.success
    assert len(error_result.errors) == 2


def test_nullable_int():
    assert not eval_config_value_from_dagster_type(Int, None).success
    assert eval_config_value_from_dagster_type(Int, 0).success
    assert eval_config_value_from_dagster_type(Int, 1).success

    assert eval_config_value_from_dagster_type(Nullable(Int), None).success
    assert eval_config_value_from_dagster_type(Nullable(Int), 0).success
    assert eval_config_value_from_dagster_type(Nullable(Int), 1).success


def test_nullable_list():
    list_of_ints = List(Int)

    assert not eval_config_value_from_dagster_type(list_of_ints, None).success
    assert eval_config_value_from_dagster_type(list_of_ints, []).success
    assert not eval_config_value_from_dagster_type(list_of_ints, [None]).success
    assert eval_config_value_from_dagster_type(list_of_ints, [1]).success

    nullable_list_of_ints = Nullable(List(Int))

    assert eval_config_value_from_dagster_type(nullable_list_of_ints, None).success
    assert eval_config_value_from_dagster_type(nullable_list_of_ints, []).success
    assert not eval_config_value_from_dagster_type(nullable_list_of_ints, [None]).success
    assert eval_config_value_from_dagster_type(nullable_list_of_ints, [1]).success

    list_of_nullable_ints = List(Nullable(Int))

    assert not eval_config_value_from_dagster_type(list_of_nullable_ints, None).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, []).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, [None]).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, [1]).success

    nullable_list_of_nullable_ints = Nullable(List(Nullable(Int)))

    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, None).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, []).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, [None]).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, [1]).success


def test_nullable_dict():
    dict_with_int = Dict({'int_field': Field(Int)})

    assert not eval_config_value_from_dagster_type(dict_with_int, None).success
    assert not eval_config_value_from_dagster_type(dict_with_int, {}).success
    assert not eval_config_value_from_dagster_type(dict_with_int, {'int_field': None}).success
    assert eval_config_value_from_dagster_type(dict_with_int, {'int_field': 1}).success

    nullable_dict_with_int = Nullable(Dict({'int_field': Field(Int)}))

    assert eval_config_value_from_dagster_type(nullable_dict_with_int, None).success
    assert not eval_config_value_from_dagster_type(nullable_dict_with_int, {}).success
    assert not eval_config_value_from_dagster_type(
        nullable_dict_with_int, {'int_field': None}
    ).success
    assert eval_config_value_from_dagster_type(nullable_dict_with_int, {'int_field': 1}).success

    dict_with_nullable_int = Dict({'int_field': Field(Nullable(Int))})

    assert not eval_config_value_from_dagster_type(dict_with_nullable_int, None).success
    assert not eval_config_value_from_dagster_type(dict_with_nullable_int, {}).success
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {'int_field': None}).success
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {'int_field': 1}).success

    nullable_dict_with_nullable_int = Nullable(Dict({'int_field': Field(Nullable(Int))}))

    assert eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, None).success
    assert not eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, {}).success
    assert eval_config_value_from_dagster_type(
        nullable_dict_with_nullable_int, {'int_field': None}
    ).success
    assert eval_config_value_from_dagster_type(
        nullable_dict_with_nullable_int, {'int_field': 1}
    ).success


def test_any_with_default_value():
    dict_with_any = Dict({'any_field': Field(Any, default_value='foo', is_optional=True)})
    result = eval_config_value_from_dagster_type(dict_with_any, None)
    assert result.success
    assert result.value == {'any_field': 'foo'}
