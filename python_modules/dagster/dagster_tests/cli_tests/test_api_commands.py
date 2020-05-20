from click.testing import CliRunner

from dagster import file_relative_path, seven
from dagster.cli.api import (
    execute_run_command,
    pipeline_snapshot_command,
    repository_snapshot_command,
)
from dagster.core.host_representation import ExternalPipelineData, ExternalRepositoryData
from dagster.core.instance import DagsterInstance
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import IPCEndMessage, IPCStartMessage
from dagster.utils import safe_tempfile_path


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


def test_execute_run_command():
    runner = CliRunner()

    with safe_tempfile_path() as filename:
        with seven.TemporaryDirectory() as temp_dir:
            instance = DagsterInstance.local_temp(temp_dir)
            pipeline_run = instance.create_run(
                pipeline_name='foo', environment_dict={}, mode='default',
            )
            result = runner.invoke(
                execute_run_command,
                [
                    '-y',
                    file_relative_path(__file__, 'repository_file.yaml'),
                    filename,
                    "--instance-ref={instance_ref_json}".format(
                        instance_ref_json=serialize_dagster_namedtuple(instance.get_ref())
                    ),
                    '--pipeline-run={pipeline_run}'.format(
                        pipeline_run=serialize_dagster_namedtuple(pipeline_run)
                    ),
                ],
            )

            assert result.exit_code == 0

            with open(filename, 'r') as f:
                # Read lines from output file, and strip newline characters
                lines = [line.rstrip() for line in f.readlines()]

                assert len(lines) == 13

                # Check all lines are serialized dagster named tuples
                for line in lines:
                    deserialize_json_to_dagster_namedtuple(line)

                # Check for start ane dnd messages
                assert deserialize_json_to_dagster_namedtuple(lines[0]) == IPCStartMessage()
                assert deserialize_json_to_dagster_namedtuple(lines[-1]) == IPCEndMessage()


def test_execute_pipeline_command_missing_args():
    runner = CliRunner()

    with safe_tempfile_path() as filename:
        result = runner.invoke(
            execute_run_command,
            [
                '-y',
                file_relative_path(__file__, 'repository_file.yaml'),
                filename,
                # no instance or pipeline_run
            ],
        )

        assert result.exit_code == 0

        with open(filename, 'r') as f:
            # Read lines from output file, and strip newline characters
            lines = [line.rstrip() for line in f.readlines()]
            assert len(lines) == 3

            # Check all lines are serialized dagster named tuples
            for line in lines:
                deserialize_json_to_dagster_namedtuple(line)

            assert deserialize_json_to_dagster_namedtuple(lines[0]) == IPCStartMessage()
            assert deserialize_json_to_dagster_namedtuple(lines[-1]) == IPCEndMessage()
