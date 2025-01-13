from pathlib import Path

from click.testing import CliRunner
from dagster._core.test_utils import new_cwd
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import

from dagster_components_tests.integration_tests.validation_tests.utils import (
    create_code_location_from_component,
)

ensure_dagster_components_tests_import()


def test_check_component_command():
    runner = CliRunner()

    with create_code_location_from_component(
        "validation/basic_component_success", Path(__file__).parent / "basic_components.py"
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
            assert result.exit_code == 0, str(result.stdout)


def test_check_component_command_failure():
    runner = CliRunner()

    with create_code_location_from_component(
        "validation/basic_component_invalid_value", Path(__file__).parent / "basic_components.py"
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
            assert result.exit_code != 0, str(result.stdout)

            assert "component.yaml:5" in str(result.stdout)
            assert "params.an_int" in str(result.stdout)
            assert "Input should be a valid integer" in str(result.stdout)
