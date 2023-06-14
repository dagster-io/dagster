import subprocess

from click.testing import CliRunner
from dagster_webserver.cli import dagster_webserver


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(dagster_webserver, ["--version"])
    assert "dagster-webserver, version" in result.output


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
