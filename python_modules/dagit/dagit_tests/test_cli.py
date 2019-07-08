from click.testing import CliRunner

from dagit.cli import ui


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ['--version'])
    assert 'dagit, version' in result.output
