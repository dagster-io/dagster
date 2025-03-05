import pytest
from dagster._core.instance_for_test import environ
from dagster_components.core.schema.context import ResolutionException
from dagster_components.test.test_cases import (
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
)
from dagster_components.utils import ensure_dagster_components_tests_import
from pydantic import ValidationError
from yaml.scanner import ScannerError

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs

ensure_dagster_components_tests_import()


@pytest.mark.parametrize(
    "test_case",
    COMPONENT_VALIDATION_TEST_CASES,
    ids=[str(case.component_path) for case in COMPONENT_VALIDATION_TEST_CASES],
)
def test_validation_messages(test_case: ComponentValidationTestCase) -> None:
    """Tests raw YAML error messages when attempting to load components with
    errors.
    """
    with environ({"STRING_ENV_VAR": "foo", "INT_ENV_VAR": "42"}):
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
