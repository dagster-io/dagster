import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import mock

import pytest
from dagster_dg.cli.utils import DEFAULT_SCHEMA_FOLDER_NAME
from dagster_dg.utils import ensure_dagster_dg_tests_import, filesystem

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    install_libraries_to_venv,
    isolated_example_project_foo_bar,
)


def mock_vscode_cli_command(editor, args: list[str]) -> bytes:
    return b"redhat.vscode-yaml"


@pytest.mark.parametrize("editor", ["vscode", "cursor"])
def test_utils_configure_editor(editor: str) -> None:
    with (
        ProxyRunner.test() as runner,
        TemporaryDirectory() as extension_dir,
        mock.patch("dagster_dg.utils.editor.has_editor_cli_command", new=lambda x: True),
        mock.patch("dagster_dg.utils.editor.run_editor_cli_command", new=mock_vscode_cli_command),
        mock.patch(
            "dagster_dg.utils.editor.get_default_extension_dir",
            return_value=Path(extension_dir),
        ),
        isolated_example_project_foo_bar(runner, False),
    ):
        out = runner.invoke("utils", "configure-editor", editor)

        assert out.exit_code == 0

        sample_project_dg_path = Path.cwd() / DEFAULT_SCHEMA_FOLDER_NAME
        assert (sample_project_dg_path / "schema.json").exists()

        expected_vscode_plugin_folder_filepath = Path(extension_dir) / "dagster-components-schema"
        assert expected_vscode_plugin_folder_filepath.exists()
        expected_compiled_plugin_filepath = (
            expected_vscode_plugin_folder_filepath / "dagster-components-schema.vsix"
        )
        assert expected_compiled_plugin_filepath.exists()


@pytest.mark.parametrize("output_path", [None, "schema.json"])
def test_generate_component_schema(output_path: Optional[str]) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, False),
    ):
        out = runner.invoke(
            "utils",
            "generate-component-schema",
            *(["--output-path", output_path] if output_path else []),
        )

        assert out.exit_code == 0

        sample_project_dg_path = Path.cwd() / DEFAULT_SCHEMA_FOLDER_NAME

        output_file = Path(output_path) if output_path else sample_project_dg_path / "schema.json"
        assert output_file.exists()


def test_generate_component_schema_watch() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, False) as project_dir,
    ):
        output_path = project_dir / "schema.json"
        stdout = ""

        def run_generate_component_schema(runner: ProxyRunner) -> None:
            result = runner.invoke(
                "utils",
                "generate-component-schema",
                "--watch",
                "--output-path",
                str(output_path),
                catch_exceptions=False,
            )
            nonlocal stdout
            stdout = result.stdout

        # Start the generate command in a separate thread
        generate_thread = threading.Thread(target=run_generate_component_schema, args=(runner,))
        generate_thread.daemon = True  # Make thread daemon so it exits when main thread exits
        generate_thread.start()

        time.sleep(10)  # Give the generate command time to start
        install_libraries_to_venv(
            project_dir / ".venv",
            ["libraries/dagster-dbt"],
        )
        time.sleep(10)  # Give time for the watcher to detect changes

        # Signal the watcher to exit
        filesystem.SHOULD_WATCHER_EXIT = True

        time.sleep(2)
        generate_thread.join(timeout=1)

        assert output_path.exists()
        assert "Dbt" in output_path.read_text()
