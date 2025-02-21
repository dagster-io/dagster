from pathlib import Path

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import, is_windows

ensure_dagster_dg_tests_import()
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_code_location_foo_bar,
    isolated_example_deployment_foo,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_validate_command_deployment_context_success():
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner, create_venv=True):
        runner.invoke("scaffold", "code-location", "code-location-1")
        runner.invoke("scaffold", "code-location", "code-location-2")

        result = runner.invoke("check", "definitions")
        assert result.exit_code == 0

        (
            Path("code_locations") / "code-location-1" / "code_location_1" / "definitions.py"
        ).write_text("invalid")
        result = runner.invoke("check", "definitions")
        assert result.exit_code == 1


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_validate_command_code_location_context_success():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("check", "definitions")
        assert result.exit_code == 0

        (Path("foo_bar") / "definitions.py").write_text("invalid")
        result = runner.invoke("check", "definitions")
        assert result.exit_code == 1
