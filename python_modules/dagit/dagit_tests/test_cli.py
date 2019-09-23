import subprocess

from click.testing import CliRunner
from dagit.cli import ui


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ['--version'])
    assert 'dagit, version' in result.output


def test_invoke_cli_wrapper_with_bad_option():
    process = subprocess.Popen(['dagit', '--fubar'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    assert process.returncode == 0
    assert b'Error: no such option: --fubar\n' in stderr
