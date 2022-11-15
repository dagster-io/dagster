from dagster import register_definitions

from dagster._core.definitions.register_definitions import get_module_name_of_caller


def test_include_register_definition_works():
    assert register_definitions


def invoke_get_module_name_of_caller():
    return get_module_name_of_caller()


def test_module_name_of_caller():
    test_module_name = invoke_get_module_name_of_caller()
    assert (
        test_module_name == "dagster_tests.core_tests.definitions_tests.test_register_definitions"
    )
