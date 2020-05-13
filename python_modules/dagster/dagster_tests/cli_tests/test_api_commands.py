from click.testing import CliRunner

from dagster import file_relative_path
from dagster.cli.api import pipeline_snapshot_command, repository_snapshot_command
from dagster.core.host_representation import ExternalPipelineData, ExternalRepositoryData
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def test_snapshot_command_repository():
    runner = CliRunner()
    result = runner.invoke(
        repository_snapshot_command, ['-y', file_relative_path(__file__, 'repository_file.yaml')],
    )
    assert result.exit_code == 0
    # Now that we have the snapshot make sure that it can be properly deserialized
    external_repository_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(external_repository_data, ExternalRepositoryData)
    assert external_repository_data.name == 'bar'
    assert len(external_repository_data.external_pipeline_datas) == 2


def test_snapshot_command_pipeline():
    runner = CliRunner()
    result = runner.invoke(
        pipeline_snapshot_command,
        ['-y', file_relative_path(__file__, 'repository_file.yaml'), 'foo'],
    )
    assert result.exit_code == 0
    # Now that we have the snapshot make sure that it can be properly deserialized
    external_pipeline_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(external_pipeline_data, ExternalPipelineData)
    assert external_pipeline_data.name == 'foo'
    assert (
        len(external_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps)
        == 2
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
    external_pipeline_data = deserialize_json_to_dagster_namedtuple(result.output)
    assert isinstance(external_pipeline_data, ExternalPipelineData)
    assert external_pipeline_data.name == 'foo'
    assert (
        len(external_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps)
        == 1
    )
