import threading
from typing import Optional

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import, get_venv_executable, install_to_venv

ensure_dagster_dg_tests_import()

import os
import subprocess
import time
from pathlib import Path
from unittest import mock

import requests
from dagster_dg.cli import docs

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    find_free_port,
    isolated_components_venv,
)

# ########################
# ##### COMPONENT TYPE
# ########################


@pytest.mark.parametrize("port", [None, find_free_port()])
def test_docs_component_type_success(port: Optional[int]):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        url = None

        def mock_open(url_arg):
            nonlocal url
            url = url_arg

        with mock.patch("webbrowser.open", side_effect=mock_open):

            def run_docs(runner: ProxyRunner) -> None:
                runner.invoke(
                    "docs",
                    "serve",
                    *(["--port", str(port)] if port else []),
                    catch_exceptions=True,
                )

            check_thread = threading.Thread(target=run_docs, args=(runner,))
            check_thread.daemon = True
            check_thread.start()

            while url is None:
                time.sleep(0.5)

        if port:
            assert f":{port}" in url

        docs_contents = requests.get(url).text
        assert "dagster_test.components.ComplexAssetComponent" in docs_contents
        docs.SHOULD_DOCS_EXIT = True


def _includes_ignore_indent(text: str, substr: str) -> bool:
    # ensure that the substr is present in the text, ignoring any leading whitespace on each
    # line of text
    substr_no_leading_whitespace = "\n".join([line.lstrip() for line in substr.split("\n")])
    text_no_leading_whitespace = "\n".join([line.lstrip() for line in text.split("\n")])
    return substr_no_leading_whitespace in text_no_leading_whitespace


@pytest.mark.skip(reason="New docs command does not yet support output to console")
def test_docs_component_type_success_output_console():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "docs",
            "component-type",
            "dagster_test.components.ComplexAssetComponent",
            "--output",
            "cli",
        )
        assert_runner_result(result)
        assert "<html" in result.output
        assert "An asset that has a complex schema." in result.output

        # Test that examples propagate into docs
        assert "value: example_for_value" in result.output
        assert _includes_ignore_indent(
            result.output,
            """
list_value:
    - example_for_list_value_1
    - example_for_list_value_2
        """,
        )
        assert _includes_ignore_indent(
            result.output,
            """
obj_value:
    key_1: value_1
    key_2: value_2
        """,
        )


def test_build_docs_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner) as venv_path,
    ):
        result = runner.invoke("docs", "build", str(venv_path / "built_docs"))
        assert_runner_result(result)

        assert (venv_path / "built_docs" / "index.html").exists()


def test_build_docs_success_in_published_package():
    # Tests that the logic to copy the docs webapp to the dagster-dg Python package works
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        module_dir = Path(__file__).parent.parent.parent
        root_modules_dir = Path(__file__).parent.parent.parent.parent.parent
        repo_root = root_modules_dir.parent
        component_dir = Path.cwd()

        venv_path = Path.cwd() / ".venv"
        install_to_venv(venv_path, ["build<0.10.0"])

        # Copy the docs webapp to the dagster-dg Python package
        subprocess.check_call(["make", "ready_dagster_dg_docs_for_publish"], cwd=repo_root)

        # Create a wheel mimicing the published dagster-dg package
        os.chdir(module_dir)
        subprocess.check_call(["python", "-m", "build"])
        wheel_file = next(Path("dist").glob("*.whl")).absolute()

        # Install the wheel in the venv
        os.chdir(component_dir)
        install_to_venv(venv_path, [f"dagster-dg@{wheel_file}"])

        # Build the docs using the wheel copy of the package
        executable = get_venv_executable(venv_path, "dg")
        subprocess.check_call(["corepack", "enable"])
        subprocess.check_call([str(executable), "docs", "build", component_dir / "built_docs"])

        assert (component_dir / "built_docs" / "index.html").exists()
