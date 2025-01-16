from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, isolated_example_code_location_bar


def mock_vscode_cli_command(args: list[str]) -> bytes:
    return b"redhat.vscode-yaml"


def test_configure_vscode() -> None:
    with (
        ProxyRunner.test() as runner,
        TemporaryDirectory() as extension_dir,
        mock.patch(
            "dagster_dg.cli.vscode_utils.run_vscode_cli_command", new=mock_vscode_cli_command
        ),
        mock.patch(
            "dagster_dg.cli.vscode_utils.get_default_extension_dir",
            return_value=Path(extension_dir),
        ),
        isolated_example_code_location_bar(runner, False) as path,
    ):
        out = runner.invoke("code-location", "configure-vscode")

        assert out.exit_code == 0

        sample_project_vscode_path = path / ".vscode"
        assert (sample_project_vscode_path / "schema.json").exists()

        expected_vscode_plugin_folder_filepath = Path(extension_dir) / "dagster-components-schema"
        assert expected_vscode_plugin_folder_filepath.exists()
        expected_compiled_plugin_filepath = (
            expected_vscode_plugin_folder_filepath / "dagster-components-schema.vsix"
        )
        assert expected_compiled_plugin_filepath.exists()
