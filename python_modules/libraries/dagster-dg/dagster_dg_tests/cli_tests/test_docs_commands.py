import threading
from typing import Optional

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

import time
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
