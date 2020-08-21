from click.testing import CliRunner

from dagster.cli.pipeline import pipeline_list_command
from dagster.utils import script_relative_path


def no_print(_):
    return None


def test_list_command():
    runner = CliRunner()

    result = runner.invoke(pipeline_list_command, ["-w", script_relative_path("../workspace.yaml")])
    assert result.exit_code == 0
