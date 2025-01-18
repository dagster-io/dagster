from pathlib import Path

import pytest
from click.testing import CliRunner
from dagster._core.test_utils import new_cwd
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import
from pydantic import ValidationError

from dagster_components_tests.integration_tests.validation_tests.test_cases import (
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
)
from dagster_components_tests.integration_tests.validation_tests.utils import (
    create_code_location_from_components,
    load_test_component_defs_inject_component,
)

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
    if test_case.should_error:
        with pytest.raises(ValidationError) as e:
            load_test_component_defs_inject_component(
                str(test_case.component_path),
                test_case.component_type_filepath,
            )

        assert test_case.validate_error_msg
        test_case.validate_error_msg(str(e.value))
    else:
        load_test_component_defs_inject_component(
            str(test_case.component_path),
            test_case.component_type_filepath,
        )


@pytest.mark.parametrize(
    "test_case",
    COMPONENT_VALIDATION_TEST_CASES,
    ids=[str(case.component_path) for case in COMPONENT_VALIDATION_TEST_CASES],
)
def test_validation_cli(test_case: ComponentValidationTestCase) -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    runner = CliRunner()

    with create_code_location_from_components(
        test_case.component_path, local_component_defn_to_inject=test_case.component_type_filepath
    ) as tmpdir:
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "check",
                    "component",
                ],
                catch_exceptions=False,
            )
            if test_case.should_error:
                assert result.exit_code != 0, str(result.stdout)

                assert test_case.validate_error_msg
                test_case.validate_error_msg(str(result.stdout))

                if test_case.validate_error_msg_additional_cli:
                    test_case.validate_error_msg_additional_cli(str(result.stdout))
            else:
                assert result.exit_code == 0, str(result.stdout)


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
    runner = CliRunner()

    with create_code_location_from_components(
        BASIC_MISSING_VALUE.component_path,
        BASIC_INVALID_VALUE.component_path,
        local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
    ) as tmpdir:
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "check",
                    "component",
                    *(
                        [
                            str(
                                Path("my_location") / "components" / "basic_component_missing_value"
                            ),
                            str(
                                Path("my_location") / "components" / "basic_component_invalid_value"
                            ),
                        ]
                        if scope_check_run
                        else []
                    ),
                ],
                catch_exceptions=False,
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.validate_error_msg and BASIC_MISSING_VALUE.validate_error_msg
            BASIC_INVALID_VALUE.validate_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.validate_error_msg(str(result.stdout))


def test_validation_cli_multiple_components_filter() -> None:
    """Ensure that the check CLI filters components to validate based on the provided paths."""
    runner = CliRunner()

    with create_code_location_from_components(
        BASIC_MISSING_VALUE.component_path,
        BASIC_INVALID_VALUE.component_path,
        local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
    ) as tmpdir:
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "check",
                    "component",
                    str(Path("my_location") / "components" / "basic_component_missing_value"),
                ],
                catch_exceptions=False,
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.validate_error_msg and BASIC_MISSING_VALUE.validate_error_msg

            BASIC_MISSING_VALUE.validate_error_msg(str(result.stdout))
            # We exclude the invalid value test case
            with pytest.raises(AssertionError):
                BASIC_INVALID_VALUE.validate_error_msg(str(result.stdout))
