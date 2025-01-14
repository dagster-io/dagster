from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ComponentValidationTestCase:
    """A test case for validating a component, used to
    test raw YAML error messages as well as the check CLI.
    """

    component_path: str
    component_type_filepath: Path
    should_error: bool
    validate_error_msg: Optional[Callable[[str], None]] = None
    validate_error_msg_additional_cli: Optional[Callable[[str], None]] = None


def msg_includes_all_of(*substrings: str) -> Callable[[str], None]:
    def _validate_error_msg(msg: str) -> None:
        for substring in substrings:
            assert substring in msg, f"Expected '{substring}' to be in error message '{msg}'"

    return _validate_error_msg


BASIC_INVALID_VALUE = ComponentValidationTestCase(
    component_path="validation/basic_component_invalid_value",
    component_type_filepath=Path(__file__).parent / "basic_components.py",
    should_error=True,
    validate_error_msg=msg_includes_all_of(
        "component.yaml:5", "params.an_int", "Input should be a valid integer"
    ),
)

BASIC_MISSING_VALUE = ComponentValidationTestCase(
    component_path="validation/basic_component_missing_value",
    component_type_filepath=Path(__file__).parent / "basic_components.py",
    should_error=True,
    validate_error_msg=msg_includes_all_of("component.yaml:4", "params.an_int", "required"),
    validate_error_msg_additional_cli=msg_includes_all_of(
        "Field `an_int` is required but not provided"
    ),
)

COMPONENT_VALIDATION_TEST_CASES = [
    ComponentValidationTestCase(
        component_path="validation/basic_component_success",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=False,
    ),
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    ComponentValidationTestCase(
        component_path="validation/basic_component_extra_value",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:7", "params.a_bool", "Extra inputs are not permitted"
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_invalid_values",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:7",
            "params.nested.foo.an_int",
            "Input should be a valid integer",
            "component.yaml:12",
            "params.nested.baz.a_string",
            "Input should be a valid string",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_missing_values",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:6", "params.nested.foo.an_int", "required"
        ),
        validate_error_msg_additional_cli=msg_includes_all_of(
            "Field `a_string` is required but not provided"
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/nested_component_extra_values",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:8",
            "params.nested.foo.a_bool",
            "Extra inputs are not permitted",
            "component.yaml:15",
            "params.nested.baz.another_bool",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/invalid_component_file_model",
        component_type_filepath=Path(__file__).parent / "basic_components.py",
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:1",
            "type",
            "Input should be a valid string",
            "component.yaml:3",
            "params",
            "Input should be an object",
        ),
    ),
]
