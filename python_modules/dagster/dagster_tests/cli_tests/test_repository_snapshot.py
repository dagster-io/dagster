import pytest
from click.testing import CliRunner

from dagster import file_relative_path
from dagster.check import ParameterCheckError
from dagster.cli.repository import snapshot_command
from dagster.core.snap.repository_snapshot import RepositorySnapshot
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils import safe_tempfile_path


def test_snapshot_command_handle_repository():
    runner = CliRunner()
    with safe_tempfile_path() as fp:
        result = runner.invoke(
            snapshot_command, [fp, '-y', file_relative_path(__file__, 'repository_file.yaml')],
        )
        assert result.exit_code == 0
        # Now that we have the snapshot make sure that it can be properly deserialized
        with open(fp) as buffer:
            repository_snap = deserialize_json_to_dagster_namedtuple(buffer.read())
        assert isinstance(repository_snap, RepositorySnapshot)
        assert repository_snap.name == 'bar'
        assert len(repository_snap.pipeline_snapshots) == 2


def test_snapshot_command_error_on_pipeline_definition():
    runner = CliRunner()
    with pytest.raises(ParameterCheckError):
        with safe_tempfile_path() as fp:
            result = runner.invoke(
                snapshot_command,
                [
                    fp,
                    '-f',
                    file_relative_path(__file__, 'test_cli_commands.py'),
                    '-n',
                    'baz_pipeline',
                ],
            )
            assert result.exit_code == 1
            raise result.exception
