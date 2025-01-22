from pathlib import Path

import pytest
from dagster._core.test_utils import new_cwd
from dagster_components.utils import ensure_dagster_components_tests_import
from dagster_components_tests.integration_tests.validation_tests.test_cases import (
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
)
from dagster_components_tests.utils import create_code_location_from_components
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg_tests.utils import ProxyRunner

ensure_dagster_components_tests_import()
ensure_dagster_dg_tests_import()


@pytest.mark.parametrize(
    "test_case",
    COMPONENT_VALIDATION_TEST_CASES,
    ids=[str(case.component_path) for case in COMPONENT_VALIDATION_TEST_CASES],
)
def test_validation_cli(test_case: ComponentValidationTestCase) -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            test_case.component_path,
            local_component_defn_to_inject=test_case.component_type_filepath,
        ) as tmpdir,
    ):
        with new_cwd(str(tmpdir)):
            result = runner.invoke("component", "check")
            if test_case.should_error:
                assert result.exit_code != 0, str(result.stdout)

                assert test_case.check_error_msg
                test_case.check_error_msg(str(result.stdout))

            else:
                assert result.exit_code == 0


@pytest.mark.parametrize(
    "scope_check_run",
    [True, False],
)
def test_validation_cli_multiple_components(scope_check_run: bool) -> None:
    """Ensure that the check CLI can validate multiple components in a single code location, and
    that error messages from all components are displayed.

    The parameter `scope_check_run` determines whether the check CLI is run pointing at both
    components or none (defaulting to the entire workspace) - the output should be the same in
    either case, this just tests that the CLI can handle multiple filters.
    """
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                "component",
                "check",
                *(
                    [
                        str(Path("my_location") / "components" / "basic_component_missing_value"),
                        str(Path("my_location") / "components" / "basic_component_invalid_value"),
                    ]
                    if scope_check_run
                    else []
                ),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


def test_validation_cli_multiple_components_filter() -> None:
    """Ensure that the check CLI filters components to validate based on the provided paths."""
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                "component",
                "check",
                str(Path("my_location") / "components" / "basic_component_missing_value"),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg

            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))
            # We exclude the invalid value test case
            with pytest.raises(AssertionError):
                BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
