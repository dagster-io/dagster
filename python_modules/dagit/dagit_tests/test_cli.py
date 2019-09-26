import subprocess

from click.testing import CliRunner
from dagit.cli import ui

from dagster.utils import script_relative_path


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ['--version'])
    assert 'dagit, version' in result.output


def test_invoke_ui_bad_no_watch():
    runner = CliRunner()
    result = runner.invoke(ui, ['--no-watch', '-y', script_relative_path('repository.yaml')])
    assert result.exit_code == 2
    assert 'Do not set no_watch when calling the Dagit Python CLI directly' in str(result.stdout)


def test_invoke_cli_wrapper_with_bad_option():
    process = subprocess.Popen(['dagit', '--fubar'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    assert process.returncode == 0
    assert b'Error: no such option: --fubar\n' in stderr
