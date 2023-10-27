import os
import subprocess

import pytest
from click.testing import CliRunner
from dagster_webserver.cli import dagster_webserver


def test_invoke_cli():
    runner = CliRunner()
    result = runner.invoke(dagster_webserver, ["--version"])
    assert "dagster-webserver, version" in result.output


@pytest.mark.parametrize("prefix", ["DAGSTER_WEBSERVER", "DAGIT"])
def test_invoke_cli_with_env_var_options(prefix):
    process = subprocess.Popen(
        ["dagster-webserver"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, f"{prefix}_VERSION": "1"},
    )
    stdout, _ = process.communicate()
    assert process.returncode == 0
    assert b"dagster-webserver, version" in stdout.lower()


def test_invoke_cli_wrapper_with_nonexistant_option():
    process = subprocess.Popen(
        ["dagster-webserver", "--fubar"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    assert process.returncode != 0
    assert b"error: no such option: --fubar\n" in stderr.lower()


def test_invoke_cli_wrapper_with_invalid_option():
    process = subprocess.Popen(
        ["dagster-webserver", "-d", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    assert process.returncode != 0
    assert (
        b"Error: Invalid set of CLI arguments for loading repository/job. See --help for details.\n"
        in stderr
    )
