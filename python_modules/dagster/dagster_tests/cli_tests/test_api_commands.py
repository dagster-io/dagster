import pytest
from click.testing import CliRunner

from dagster import file_relative_path
from dagster.check import ParameterCheckError
from dagster.cli.api import pipeline_snapshot_command, repository_snapshot_command
from dagster.core.snap import ActiveRepositoryData
from dagster.core.snap.active_data import ActivePipelineData
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def test_snapshot_command_repository():
    runner = CliRunner()
    result = runner.invoke(
        repository_snapshot_command, ['-y', file_relative_path(__file__, 'repository_file.yaml')],
    )
    assert result.exit_code == 0
    # Now that we have the snapshot make sure that it can be properly deserialized
    active_repository_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(active_repository_data, ActiveRepositoryData)
    assert active_repository_data.name == 'bar'
    assert len(active_repository_data.active_pipeline_datas) == 2


def test_snapshot_command_repository_fail_on_pipeline_handle():
    runner = CliRunner()
    with pytest.raises(ParameterCheckError):
        result = runner.invoke(
            repository_snapshot_command,
            ['-f', file_relative_path(__file__, 'test_cli_commands.py'), '-n', 'baz_pipeline',],
        )
        assert result.exit_code == 1
        raise result.exception


def test_snapshot_command_pipeline():
    runner = CliRunner()
    result = runner.invoke(
        pipeline_snapshot_command,
        ['-y', file_relative_path(__file__, 'repository_file.yaml'), 'foo'],
    )
    assert result.exit_code == 0
    # Now that we have the snapshot make sure that it can be properly deserialized
    active_pipeline_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(active_pipeline_data, ActivePipelineData)
    assert active_pipeline_data.name == 'foo'
    assert (
        len(active_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps) == 2
    )


def test_snapshot_command_pipeline_solid_subset():
    runner = CliRunner()
    result = runner.invoke(
        pipeline_snapshot_command,
        [
            '-y',
            file_relative_path(__file__, 'repository_file.yaml'),
            'foo',
            '--solid-subset',
            'do_input',
        ],
    )
    assert result.exit_code == 0
    # Now that we have the snapshot make sure that it can be properly deserialized
    active_pipeline_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(active_pipeline_data, ActivePipelineData)
    assert active_pipeline_data.name == 'foo'
    assert (
        len(active_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps) == 1
    )
