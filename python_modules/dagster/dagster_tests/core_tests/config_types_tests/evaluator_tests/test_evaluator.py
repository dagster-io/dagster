from dagster import Any, Bool, Field, Int, Noneable, Selector, Shape, String, StringSource
from dagster._config import (
    DagsterEvaluationErrorReason,
    EvaluateValueResult,
    EvaluationStackListItemEntry,
    EvaluationStackMapKeyEntry,
    EvaluationStackMapValueEntry,
    EvaluationStackPathEntry,
    process_config,
    resolve_to_config_type,
)


def eval_config_value_from_dagster_type(dagster_type, value):
    return process_config(resolve_to_config_type(dagster_type), value)


def assert_success(result, expected_value):
    assert result.success
    assert result.value == expected_value


def test_evaluate_scalar_success():
    assert_success(eval_config_value_from_dagster_type(String, "foobar"), "foobar")
    assert_success(eval_config_value_from_dagster_type(Int, 34234), 34234)
    assert_success(eval_config_value_from_dagster_type(Bool, True), True)


def test_evaluate_scalar_failure():
    result = eval_config_value_from_dagster_type(String, 2343)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries
    assert error.error_data.config_type_snap.given_name == "String"  # pyright: ignore[reportAttributeAccessIssue]
    assert error.error_data.value_rep == "2343"  # pyright: ignore[reportAttributeAccessIssue]


SingleLevelShape = Shape({"level_one": Field(String)})


def test_single_error():
    success_value = {"level_one": "ksjdfd"}
    assert_success(
        eval_config_value_from_dagster_type(SingleLevelShape, success_value), success_value
    )


def test_single_level_scalar_mismatch():
    value = {"level_one": 234}
    result = eval_config_value_from_dagster_type(SingleLevelShape, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 1
    assert error.stack.entries[0].field_name == "level_one"  # pyright: ignore[reportAttributeAccessIssue]


def test_single_level_dict_not_a_dict():
    value = "not_a_dict"
    result = eval_config_value_from_dagster_type(SingleLevelShape, value)
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert not error.stack.entries


def test_root_missing_field():
    result = eval_config_value_from_dagster_type(SingleLevelShape, {})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert len(result.errors_at_level()) == 1
    assert error.error_data.field_name == "level_one"  # pyright: ignore[reportAttributeAccessIssue]


DoubleLevelShape = Shape(
    {
        "level_one": Field(
            Shape(
                {
                    "string_field": Field(String),
                    "int_field": Field(Int, is_required=False, default_value=989),
                    "bool_field": Field(Bool),
                }
            )
        )
    }
)


def test_nested_success():
    value = {"level_one": {"string_field": "skdsjfkdj", "int_field": 123, "bool_field": True}}

    assert_success(eval_config_value_from_dagster_type(DoubleLevelShape, value), value)

    result = eval_config_value_from_dagster_type(
        DoubleLevelShape, {"level_one": {"string_field": "kjfkd", "bool_field": True}}
    )

    assert isinstance(result, EvaluateValueResult)

    assert result.success
    assert result.value["level_one"]["int_field"] == 989  # pyright: ignore[reportOptionalSubscript]


def test_nested_error_one_field_not_defined():
    value = {
        "level_one": {
            "string_field": "skdsjfkdj",
            "int_field": 123,
            "bool_field": True,
            "no_field_one": "kdjfkd",
        }
    }

    result = eval_config_value_from_dagster_type(DoubleLevelShape, value)

    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert error.error_data.field_name == "no_field_one"  # pyright: ignore[reportAttributeAccessIssue]
    assert len(error.stack.entries) == 1
    stack_entry = error.stack.entries[0]
    assert stack_entry.field_name == "level_one"  # pyright: ignore[reportAttributeAccessIssue]


def get_field_name_error(result, field_name):
    for error in result.errors:
        if error.error_data.field_name == field_name:
            return error
    assert False


def test_nested_error_two_fields_not_defined():
    value = {
        "level_one": {
            "string_field": "skdsjfkdj",
            "int_field": 123,
            "bool_field": True,
            "no_field_one": "kdjfkd",
            "no_field_two": "kdjfkd",
        }
    }

    result = eval_config_value_from_dagster_type(DoubleLevelShape, value)

    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]

    fields_error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]

    assert fields_error.reason == DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED

    assert fields_error.error_data.field_names == ["no_field_one", "no_field_two"]  # pyright: ignore[reportAttributeAccessIssue]


def test_nested_error_missing_fields():
    value = {"level_one": {"string_field": "skdsjfkdj"}}

    result = eval_config_value_from_dagster_type(DoubleLevelShape, value)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert error.error_data.field_name == "bool_field"  # pyright: ignore[reportAttributeAccessIssue]


def test_nested_error_multiple_missing_fields():
    value = {"level_one": {}}

    result = eval_config_value_from_dagster_type(DoubleLevelShape, value)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]

    fields_error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert fields_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    assert fields_error.error_data.field_names == ["bool_field", "string_field"]  # pyright: ignore[reportAttributeAccessIssue]


def test_nested_missing_and_not_defined():
    value = {"level_one": {"not_defined": "kjdfkdj"}}

    result = eval_config_value_from_dagster_type(DoubleLevelShape, value)
    assert not result.success
    assert len(result.errors) == 2  # pyright: ignore[reportArgumentType]

    fields_error = next(
        error
        for error in result.errors  # pyright: ignore[reportOptionalIterable]
        if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    )

    assert fields_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS
    assert fields_error.error_data.field_names == ["bool_field", "string_field"]  # pyright: ignore[reportAttributeAccessIssue]

    assert (
        get_field_name_error(result, "not_defined").reason
        == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    )


MultiLevelShapeType = Shape(
    {
        "level_one_string_field": String,
        "level_two_dict": {
            "level_two_int_field": Int,
            "level_three_dict": {"level_three_string": String},
        },
    }
)


def test_multilevel_success():
    working_value = {
        "level_one_string_field": "foo",
        "level_two_dict": {
            "level_two_int_field": 234234,
            "level_three_dict": {"level_three_string": "kjdfkd"},
        },
    }

    assert_success(
        eval_config_value_from_dagster_type(MultiLevelShapeType, working_value), working_value
    )


def test_deep_scalar():
    value = {
        "level_one_string_field": "foo",
        "level_two_dict": {
            "level_two_int_field": 234234,
            "level_three_dict": {"level_three_string": 123},
        },
    }

    result = eval_config_value_from_dagster_type(MultiLevelShapeType, value)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert error.error_data.config_type_snap.given_name == "String"  # pyright: ignore[reportAttributeAccessIssue]
    assert error.error_data.value_rep == "123"  # pyright: ignore[reportAttributeAccessIssue]
    assert len(error.stack.entries) == 3

    assert [entry.field_name for entry in error.stack.entries] == [  # pyright: ignore[reportAttributeAccessIssue]
        "level_two_dict",
        "level_three_dict",
        "level_three_string",
    ]

    assert not result.errors_at_level("level_one_string_field")
    assert not result.errors_at_level("level_two_dict")
    assert not result.errors_at_level("level_two_dict", "level_three_dict")
    assert (
        len(result.errors_at_level("level_two_dict", "level_three_dict", "level_three_string")) == 1
    )


def test_deep_mixed_level_errors():
    value = {
        "level_one_string_field": "foo",
        "level_one_not_defined": "kjsdkfjd",
        "level_two_dict": {
            # 'level_two_int_field': 234234, # missing
            "level_three_dict": {"level_three_string": 123}
        },
    }

    result = eval_config_value_from_dagster_type(MultiLevelShapeType, value)
    assert not result.success
    assert len(result.errors) == 3  # pyright: ignore[reportArgumentType]

    root_errors = result.errors_at_level()
    assert len(root_errors) == 1
    root_error = root_errors[0]
    assert root_error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert root_error.error_data.field_name == "level_one_not_defined"  # pyright: ignore[reportAttributeAccessIssue]

    level_two_errors = result.errors_at_level("level_two_dict")
    assert len(level_two_errors) == 1
    level_two_error = level_two_errors[0]
    assert level_two_error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert level_two_error.error_data.field_name == "level_two_int_field"  # pyright: ignore[reportAttributeAccessIssue]

    assert not result.errors_at_level("level_two_dict", "level_three_dict")

    final_level_errors = result.errors_at_level(
        "level_two_dict", "level_three_dict", "level_three_string"
    )

    assert len(final_level_errors) == 1
    final_level_error = final_level_errors[0]

    assert final_level_error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


ExampleSelector = Selector({"option_one": Field(String), "option_two": Field(String)})


def test_example_selector_success():
    result = eval_config_value_from_dagster_type(ExampleSelector, {"option_one": "foo"})
    assert result.success
    assert result.value == {"option_one": "foo"}

    result = eval_config_value_from_dagster_type(ExampleSelector, {"option_two": "foo"})
    assert result.success
    assert result.value == {"option_two": "foo"}


def test_example_selector_error_top_level_type():
    result = eval_config_value_from_dagster_type(ExampleSelector, "kjsdkf")
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH  # pyright: ignore[reportOptionalSubscript]


def test_example_selector_wrong_field():
    result = eval_config_value_from_dagster_type(ExampleSelector, {"nope": 234})
    assert not result.success
    assert result.value is None
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED  # pyright: ignore[reportOptionalSubscript]


def test_example_selector_multiple_fields():
    result = eval_config_value_from_dagster_type(
        ExampleSelector, {"option_one": "foo", "option_two": "boo"}
    )

    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR  # pyright: ignore[reportOptionalSubscript]


def test_selector_within_dict_no_subfields():
    result = eval_config_value_from_dagster_type(
        Shape({"selector": Field(ExampleSelector)}), {"selector": {}}
    )
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert (
        result.errors[0].message  # pyright: ignore[reportOptionalSubscript]
        == "Must specify a field at path root:selector if more than one field "
        "is defined. Defined fields: ['option_one', 'option_two']"
    )


SelectorWithDefaults = Selector({"default": Field(String, is_required=False, default_value="foo")})


def test_selector_with_defaults():
    result = eval_config_value_from_dagster_type(SelectorWithDefaults, {})
    assert result.success
    assert result.value == {"default": "foo"}


def test_evaluate_map_string():
    string_map = {str: str}
    result = eval_config_value_from_dagster_type(string_map, {"foo": "bar"})
    assert result.success
    assert result.value == {"foo": "bar"}


def test_evaluate_map_int():
    int_map = {int: str}
    result = eval_config_value_from_dagster_type(int_map, {5: "bar"})
    assert result.success
    assert result.value == {5: "bar"}


def test_evaluate_map_bool():
    int_map = {bool: float}
    result = eval_config_value_from_dagster_type(int_map, {False: 5.5})
    assert result.success
    assert result.value == {False: 5.5}


def test_evaluate_map_float():
    int_map = {float: bool}
    result = eval_config_value_from_dagster_type(int_map, {5.5: True})
    assert result.success
    assert result.value == {5.5: True}


def test_evaluate_map_error_item_mismatch():
    result = eval_config_value_from_dagster_type({str: str}, {"a": 1})
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH  # pyright: ignore[reportOptionalSubscript]


def test_evaluate_map_error_top_level_mismatch():
    string_map = {str: str}
    result = eval_config_value_from_dagster_type(string_map, 1)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH  # pyright: ignore[reportOptionalSubscript]


def test_evaluate_double_map():
    string_double_map = {int: {str: str}}
    result = eval_config_value_from_dagster_type(string_double_map, {5: {"b": "foo"}})
    assert result.success
    assert result.value == {5: {"b": "foo"}}


def test_config_map_in_dict():
    nested_map = {"nested_map": {str: int}}

    value = {"nested_map": {"a": 1, "b": 2, "c": 3}}
    result = eval_config_value_from_dagster_type(nested_map, value)
    assert result.success
    assert result.value == value


def test_config_map_in_dict_error():
    nested_map = {"nested_map": {str: int}}

    value = {"nested_map": {"a": 1, "b": "bar", "c": 3}}
    result = eval_config_value_from_dagster_type(nested_map, value)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 2
    stack_entry = error.stack.entries[0]
    assert isinstance(stack_entry, EvaluationStackPathEntry)
    assert stack_entry.field_name == "nested_map"
    map_entry = error.stack.entries[1]
    assert isinstance(map_entry, EvaluationStackMapValueEntry)
    assert map_entry.map_key == "b"


def test_config_map_in_dict_error_two_errors():
    nested_map = {"nested_map": {str: int}}

    value = {"nested_map": {"a": 1, 5: 3, "c": "bar"}}
    result = eval_config_value_from_dagster_type(nested_map, value)
    assert not result.success
    assert len(result.errors) == 2  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 2
    stack_entry = error.stack.entries[0]
    assert isinstance(stack_entry, EvaluationStackPathEntry)
    assert stack_entry.field_name == "nested_map"
    map_entry = error.stack.entries[1]
    assert isinstance(map_entry, EvaluationStackMapKeyEntry)
    assert map_entry.map_key == 5
    map_entry = result.errors[1].stack.entries[1]  # pyright: ignore[reportOptionalSubscript]
    assert isinstance(map_entry, EvaluationStackMapValueEntry)
    assert map_entry.map_key == "c"


def test_config_double_map():
    nested_maps = {
        "nested_map_one": {str: int},
        "nested_map_two": {int: str},
    }

    value = {
        "nested_map_one": {"a": 1, "b": 2, "c": 3},
        "nested_map_two": {1: "foo", 2: "bar"},
    }

    result = eval_config_value_from_dagster_type(nested_maps, value)
    assert result.success
    assert result.value == value

    error_value = {
        "nested_map_one": "kjdfkdj",
        "nested_map_two": {1: "bar"},
    }

    error_result = eval_config_value_from_dagster_type(nested_maps, error_value)
    assert not error_result.success


def test_config_double_map_double_error():
    nested_maps = {
        "nested_map_one": {str: int},
        "nested_map_two": {str: str},
    }

    error_value = {
        "nested_map_one": "kjdfkdj",
        "nested_map_two": {"x": "bar", 2: "y"},
    }
    error_result = eval_config_value_from_dagster_type(nested_maps, error_value)
    assert not error_result.success
    assert len(error_result.errors) == 2  # pyright: ignore[reportArgumentType]


def test_evaluate_list_string():
    string_list = [str]
    result = eval_config_value_from_dagster_type(string_list, ["foo"])
    assert result.success
    assert result.value == ["foo"]


def test_evaluate_list_error_item_mismatch():
    result = eval_config_value_from_dagster_type([str], [1])
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH  # pyright: ignore[reportOptionalSubscript]


def test_evaluate_list_error_top_level_mismatch():
    string_list = [str]
    result = eval_config_value_from_dagster_type(string_list, 1)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    assert result.errors[0].reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH  # pyright: ignore[reportOptionalSubscript]


def test_evaluate_double_list():
    string_double_list = [[str]]
    result = eval_config_value_from_dagster_type(string_double_list, [["foo"]])
    assert result.success
    assert result.value == [["foo"]]


def test_config_list_in_dict():
    nested_list = {"nested_list": [int]}

    value = {"nested_list": [1, 2, 3]}
    result = eval_config_value_from_dagster_type(nested_list, value)
    assert result.success
    assert result.value == value


def test_config_list_in_dict_error():
    nested_list = {"nested_list": [int]}

    value = {"nested_list": [1, "bar", 3]}
    result = eval_config_value_from_dagster_type(nested_list, value)
    assert not result.success
    assert len(result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH
    assert len(error.stack.entries) == 2
    stack_entry = error.stack.entries[0]
    assert isinstance(stack_entry, EvaluationStackPathEntry)
    assert stack_entry.field_name == "nested_list"
    list_entry = error.stack.entries[1]
    assert isinstance(list_entry, EvaluationStackListItemEntry)
    assert list_entry.list_index == 1


def test_config_double_list():
    nested_lists = {"nested_list_one": [int], "nested_list_two": [str]}

    value = {"nested_list_one": [1, 2, 3], "nested_list_two": ["foo", "bar"]}

    result = eval_config_value_from_dagster_type(nested_lists, value)
    assert result.success
    assert result.value == value

    error_value = {"nested_list_one": "kjdfkdj", "nested_list_two": ["bar"]}

    error_result = eval_config_value_from_dagster_type(nested_lists, error_value)
    assert not error_result.success


def test_config_double_list_double_error():
    nested_lists = {"nested_list_one": [int], "nested_list_two": [str]}

    error_value = {"nested_list_one": "kjdfkdj", "nested_list_two": ["bar", 2]}
    error_result = eval_config_value_from_dagster_type(nested_lists, error_value)
    assert not error_result.success
    assert len(error_result.errors) == 2  # pyright: ignore[reportArgumentType]


def test_nullable_int():
    assert not eval_config_value_from_dagster_type(Int, None).success
    assert eval_config_value_from_dagster_type(Int, 0).success
    assert eval_config_value_from_dagster_type(Int, 1).success

    assert eval_config_value_from_dagster_type(Noneable(int), None).success
    assert eval_config_value_from_dagster_type(Noneable(int), 0).success
    assert eval_config_value_from_dagster_type(Noneable(int), 1).success


def test_nullable_list():
    list_of_ints = [int]

    assert not eval_config_value_from_dagster_type(list_of_ints, None).success
    assert eval_config_value_from_dagster_type(list_of_ints, []).success
    assert not eval_config_value_from_dagster_type(list_of_ints, [None]).success
    assert eval_config_value_from_dagster_type(list_of_ints, [1]).success

    nullable_list_of_ints = Noneable([int])

    assert eval_config_value_from_dagster_type(nullable_list_of_ints, None).success
    assert eval_config_value_from_dagster_type(nullable_list_of_ints, []).success
    assert not eval_config_value_from_dagster_type(nullable_list_of_ints, [None]).success
    assert eval_config_value_from_dagster_type(nullable_list_of_ints, [1]).success

    list_of_nullable_ints = [Noneable(int)]

    assert not eval_config_value_from_dagster_type(list_of_nullable_ints, None).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, []).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, [None]).success
    assert eval_config_value_from_dagster_type(list_of_nullable_ints, [1]).success

    nullable_list_of_nullable_ints = Noneable([Noneable(int)])

    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, None).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, []).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, [None]).success
    assert eval_config_value_from_dagster_type(nullable_list_of_nullable_ints, [1]).success


def test_nullable_dict():
    dict_with_int = Shape({"int_field": Int})

    assert not eval_config_value_from_dagster_type(dict_with_int, None).success
    assert not eval_config_value_from_dagster_type(dict_with_int, {}).success
    assert not eval_config_value_from_dagster_type(dict_with_int, {"int_field": None}).success
    assert eval_config_value_from_dagster_type(dict_with_int, {"int_field": 1}).success

    nullable_dict_with_int = Noneable(Shape({"int_field": Int}))

    assert eval_config_value_from_dagster_type(nullable_dict_with_int, None).success
    assert not eval_config_value_from_dagster_type(nullable_dict_with_int, {}).success
    assert not eval_config_value_from_dagster_type(
        nullable_dict_with_int, {"int_field": None}
    ).success
    assert eval_config_value_from_dagster_type(nullable_dict_with_int, {"int_field": 1}).success

    dict_with_nullable_int = Shape({"int_field": Field(Noneable(int))})

    assert not eval_config_value_from_dagster_type(dict_with_nullable_int, None).success
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {}).success
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {}).value == {
        "int_field": None
    }
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {"int_field": None}).success
    assert eval_config_value_from_dagster_type(dict_with_nullable_int, {"int_field": 1}).success

    nullable_dict_with_nullable_int = Noneable(Shape({"int_field": Field(Noneable(int))}))

    assert eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, None).success
    assert eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, None).value is None
    assert eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, {}).success
    assert eval_config_value_from_dagster_type(nullable_dict_with_nullable_int, {}).value == {
        "int_field": None
    }
    assert eval_config_value_from_dagster_type(
        nullable_dict_with_nullable_int, {"int_field": None}
    ).success
    assert eval_config_value_from_dagster_type(
        nullable_dict_with_nullable_int, {"int_field": 1}
    ).success


def test_any_with_default_value():
    dict_with_any = Shape({"any_field": Field(Any, default_value="foo", is_required=False)})
    result = eval_config_value_from_dagster_type(dict_with_any, {})
    assert result.success
    assert result.value == {"any_field": "foo"}


def test_post_process_error():
    error_result = eval_config_value_from_dagster_type(
        Shape({"foo": StringSource}), {"foo": {"env": "THIS_ENV_VAR_DOES_NOT_EXIST"}}
    )
    assert not error_result.success
    assert len(error_result.errors) == 1  # pyright: ignore[reportArgumentType]
    error = error_result.errors[0]  # pyright: ignore[reportOptionalSubscript]
    assert error.reason == DagsterEvaluationErrorReason.FAILED_POST_PROCESSING
    assert len(error.stack.entries) == 1
