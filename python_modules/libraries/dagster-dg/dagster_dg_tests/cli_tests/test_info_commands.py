import textwrap

from click.testing import CliRunner
from dagster_dg.cli.info import info_component_type_command
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.cli_tests.test_generate_commands import isolated_example_code_location_bar


def test_info_component_type_all_metadata_success():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            info_component_type_command, ["dagster_components.pipes_subprocess_script_collection"]
        )
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent("""
                dagster_components.pipes_subprocess_script_collection

                Description:

                Assets that wrap Python scripts
        """).strip()
        )


def test_info_component_type_flag_fields_success():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            info_component_type_command,
            ["dagster_components.pipes_subprocess_script_collection", "--description"],
        )
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent("""
                Assets that wrap Python scripts
        """).strip()
        )

        result = runner.invoke(
            info_component_type_command,
            ["dagster_components.pipes_subprocess_script_collection", "--generate-params-schema"],
        )
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent("""
                No generate params schema defined.
        """).strip()
        )

        result = runner.invoke(
            info_component_type_command,
            ["dagster_components.pipes_subprocess_script_collection", "--component-params-schema"],
        )
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent("""
                No component params schema defined.
        """).strip()
        )


def test_info_component_type_outside_code_location_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            info_component_type_command, ["dagster_components.pipes_subprocess_script_collection"]
        )
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location directory" in result.output


def test_info_component_type_multiple_flags_fails() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            info_component_type_command,
            [
                "dagster_components.pipes_subprocess_script_collection",
                "--description",
                "--generate-params-schema",
            ],
        )
        assert result.exit_code != 0
        assert (
            "Only one of --description, --generate-params-schema, and --component-params-schema can be specified."
            in result.output
        )
