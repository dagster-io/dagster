import pytest
from dagster import (
    DagsterInvalidConfigDefinitionError,
    Noneable,
    Permissive,
    Selector,
    execute_solid,
    solid,
)


def test_kitchen_sink():
    @solid(
        config_schema={
            "str_field": str,
            "int_field": int,
            "list_int": [int],
            "list_list_int": [[int]],
            "dict_field": {"a_string": str},
            "list_dict_field": [{"an_int": int}],
            "selector_of_things": Selector(
                {"select_list_dict_field": [{"an_int": int}], "select_int": int}
            ),
            # this is a good argument to use () instead of [] for type parameterization in
            # the config system
            "optional_list_of_optional_string": Noneable([Noneable(str)]),
        }
    )
    def kitchen_sink(context):
        return context.solid_config

    solid_config_one = {
        "str_field": "kjf",
        "int_field": 2,
        "list_int": [3],
        "list_list_int": [[1], [2, 3]],
        "dict_field": {"a_string": "kdjfkd"},
        "list_dict_field": [{"an_int": 2}, {"an_int": 4}],
        "selector_of_things": {"select_int": 3},
        "optional_list_of_optional_string": ["foo", None],
    }

    assert (
        execute_solid(
            kitchen_sink,
            run_config={"solids": {"kitchen_sink": {"config": solid_config_one}}},
        ).output_value()
        == solid_config_one
    )

    solid_config_two = {
        "str_field": "kjf",
        "int_field": 2,
        "list_int": [3],
        "list_list_int": [[1], [2, 3]],
        "dict_field": {"a_string": "kdjfkd"},
        "list_dict_field": [{"an_int": 2}, {"an_int": 4}],
        "selector_of_things": {"select_list_dict_field": [{"an_int": 5}]},
        "optional_list_of_optional_string": None,
    }

    assert (
        execute_solid(
            kitchen_sink,
            run_config={"solids": {"kitchen_sink": {"config": solid_config_two}}},
        ).output_value()
        == solid_config_two
    )


def test_builtin_dict():
    executed = {}

    @solid(config_schema=dict)
    def builtin_dict_solid(context):
        executed["yup"] = True
        return context.solid_config

    assert isinstance(builtin_dict_solid.config_schema.config_type, Permissive)

    assert execute_solid(
        builtin_dict_solid, run_config={"solids": {"builtin_dict_solid": {"config": {"a": "b"}}}}
    ).output_value() == {"a": "b"}

    assert executed["yup"]


def test_bad_solid_config_argument():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema="dkjfkd")
        def _bad_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'dkjfkd'. 'dkjfkd' cannot be resolved."
    )


def test_bad_solid_config_argument_nested():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema={"field": "kdjkfjd"})
        def _bad_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'field': 'kdjkfjd'}. "
        "Error at stack path :field. 'kdjkfjd' cannot be resolved."
    )


def test_bad_solid_config_argument_list_wrong_length():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema={"bad_list": []})
        def _bad_list_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'bad_list': []}. "
        "Error at stack path :bad_list. [] cannot be resolved. "
        "Reason: List must be of length 1."
    )


def test_bad_solid_config_argument_list_bad_item():

    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema={"bad_list": ["kdjfkd"]})
        def _bad_list_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'bad_list': ['kdjfkd']}. "
        "Error at stack path :bad_list. ['kdjfkd'] cannot be resolved. "
        "Reason: List have a single item and contain a valid type i.e. [int]. "
        "Got item 'kdjfkd'."
    )


def test_bad_solid_config_argument_list_bad_nested_item():

    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema={"bad_nested_list": [{"bad_field": "kjdkfd"}]})
        def _bad_list_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'bad_nested_list': "
        "[{'bad_field': 'kjdkfd'}]}. Error at stack path "
        ":bad_nested_list:bad_field. 'kjdkfd' cannot be resolved."
    )
