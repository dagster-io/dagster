from click.testing import CliRunner

from dagit.cli import ui


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ['--version'])
    assert 'dagit, version' in result.output


def test_invoke_ui_bad_no_watch():
    runner = CliRunner()
    result = runner.invoke(ui, ['--no-watch'])
    assert result.exit_code == 1
    assert 'Do not set no_watch when calling the Dagit Python CLI directly' in str(result.exception)
