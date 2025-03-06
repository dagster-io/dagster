import pytest
from dagster_components.core.schema.context import ResolutionException
from dagster_components.test.test_cases import (
    BASIC_COMPONENT_TYPE_FILEPATH,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
    msg_includes_all_of,
)
from dagster_components.utils import ensure_dagster_components_tests_import
from pydantic import ValidationError
from yaml.scanner import ScannerError

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs

ensure_dagster_components_tests_import()

# extend with test cases that dont fail check yaml
DEFS_TEST_CASES = [
    *COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase(
        component_path="validation/basic_component_templating_invalid_scope",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "'fake' not found in scope",
            "component.yaml:4",
            "available scope is: env, automation_condition",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/basic_component_scope_exc",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        validate_error_msg=msg_includes_all_of(
            "component.yaml:4",
            'raise Exception("boom")',
            "_inner_error()",
        ),
    ),
]


@pytest.mark.parametrize(
    "test_case",
    DEFS_TEST_CASES,
    ids=[str(case.component_path) for case in DEFS_TEST_CASES],
)
def test_validation_messages(test_case: ComponentValidationTestCase) -> None:
    """Tests raw YAML error messages when attempting to load components with
    errors.
    """
    if test_case.should_error:
        with pytest.raises((ValidationError, ScannerError, ResolutionException)) as e:
            load_test_component_defs(
                str(test_case.component_path),
                test_case.component_type_filepath,
            )

        assert test_case.validate_error_msg
        test_case.validate_error_msg(str(e.value))
    else:
        load_test_component_defs(
            str(test_case.component_path),
            test_case.component_type_filepath,
        )
