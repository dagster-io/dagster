from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ComponentValidationTestCase:
    """A test case for validating a component, used to
    test raw YAML error messages as well as the check CLI.
    """

    component_path: str
    component_type_filepath: Optional[Path]
    should_error: bool
    validate_error_msg: Optional[Callable[[str], None]] = None
    check_error_msg: Optional[Callable[[str], None]] = None


def msg_includes_all_of(*substrings: str) -> Callable[[str], None]:
    def _validate_error_msg(msg: str) -> None:
        for substring in substrings:
            assert substring in msg, f"Expected '{substring}' to be in error message '{msg}'"

    return _validate_error_msg


BASIC_COMPONENT_TYPE_FILEPATH = Path(__file__).parent / "basic_components.py"

BASIC_INVALID_VALUE = ComponentValidationTestCase(
    component_path="validation/basic_component_invalid_value",
    component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
    should_error=True,
    validate_error_msg=msg_includes_all_of(
        "component.yaml:5", "attributes.an_int", "Input should be a valid integer"
    ),
    check_error_msg=msg_includes_all_of(
        "component.yaml:5",
        "attributes.an_int",
        "{} is not of type 'integer'",
    ),
)

BASIC_MISSING_VALUE = ComponentValidationTestCase(
    component_path="validation/basic_component_missing_value",
    component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
    should_error=True,
    validate_error_msg=msg_includes_all_of("component.yaml:3", "attributes.an_int", "required"),
    check_error_msg=msg_includes_all_of(
        "component.yaml:3",
        "attributes",
        "'an_int' is a required property",
    ),
)

BASIC_VALID_VALUE = ComponentValidationTestCase(
    component_path="validation/basic_component_success",
    component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
    should_error=False,
)

COMPONENT_VALIDATION_TEST_CASES = [
    BASIC_VALID_VALUE,
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    ComponentValidationTestCase(
        component_path="validation/basic_component_extra_value",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:7", "attributes.a_bool", "Extra inputs are not permitted"
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:7",
            "'a_bool' was unexpected",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/basic_component_extra_value_in_a_subfolder",
        component_type_filepath=None,
        should_error=True,
        validate_error_msg=msg_includes_all_of("component.yaml:4", "attributes.path"),
        check_error_msg=msg_includes_all_of(
            "component.yaml:4",
            "attributes.path",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_invalid_values",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:7",
            "attributes.nested.foo.an_int",
            "Input should be a valid integer",
            "component.yaml:12",
            "attributes.nested.baz.a_string",
            "Input should be a valid string",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:7",
            "attributes.nested.foo.an_int",
            "{} is not of type 'integer'",
            "component.yaml:12",
            "attributes.nested.baz.a_string",
            "{} is not of type 'string'",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_missing_values",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:5", "attributes.nested.foo.an_int", "required"
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:5",
            "attributes.nested.foo",
            "'an_int' is a required property",
            "component.yaml:10",
            "attributes.nested.baz",
            "'a_string' is a required property",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_extra_values",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:8",
            "attributes.nested.foo.a_bool",
            "Extra inputs are not permitted",
            "component.yaml:15",
            "attributes.nested.baz.another_bool",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:8",
            "attributes.nested.foo",
            "'a_bool' was unexpected",
            "component.yaml:15",
            "attributes.nested.baz",
            "'another_bool' was unexpected",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/invalid_component_file_model",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:1",
            "type",
            "Input should be a valid string",
            "component.yaml:3",
            "attributes",
            "Input should be an object",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:1",
            "type",
            "{} is not of type 'string'",
            "component.yaml:3",
            "attributes",
            "'asdfasdf' is not of type 'object'",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/other_invalid_component_file_model",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:3",
            "attributez",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:3",
            "attributez",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/invalid_yaml_missing_quote",
        component_type_filepath=None,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "line 2",
            "found unexpected end of stream",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:2",
            "Unable to parse YAML",
            "found unexpected end of stream",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/invalid_yaml_invalid_char",
        component_type_filepath=None,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "line 1",
            "found character '@' that cannot start any token",
        ),
        check_error_msg=msg_includes_all_of(
            "component.yaml:1",
            "Unable to parse YAML",
            "found character '@' that cannot start any token",
        ),
    ),
]
