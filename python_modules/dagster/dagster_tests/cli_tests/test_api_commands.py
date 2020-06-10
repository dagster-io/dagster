import json

from click.testing import CliRunner

from dagster import file_relative_path, seven
from dagster.cli.api import (
    execute_run_command,
    partition_data_command,
    pipeline_subset_snapshot_command,
)
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import create_run_for_test
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import IPCEndMessage, IPCStartMessage, ipc_read_event_stream
from dagster.utils import safe_tempfile_path
from dagster.utils.temp_file import get_temp_file_name


def test_snapshot_command_pipeline():
    with get_temp_file_name() as output_file:
        runner = CliRunner()
        result = runner.invoke(
            pipeline_subset_snapshot_command,
            [output_file, '-y', file_relative_path(__file__, 'repository_file.yaml'), 'foo'],
        )
        assert result.exit_code == 0
        # Now that we have the snapshot make sure that it can be properly deserialized
        messages = list(ipc_read_event_stream(output_file))
        assert len(messages) == 1
        subset_result = messages[0]
        assert isinstance(subset_result, ExternalPipelineSubsetResult)
        assert subset_result.external_pipeline_data.name == 'foo'
        assert (
            len(
                subset_result.external_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps
            )
            == 2
        )


def test_snapshot_command_pipeline_solid_selection():

    with get_temp_file_name() as output_file:
        runner = CliRunner()
        solid_selection = ['do_input']
        result = runner.invoke(
            pipeline_subset_snapshot_command,
            [
                output_file,
                '-y',
                file_relative_path(__file__, 'repository_file.yaml'),
                'foo',
                '--solid-selection={solid_selection}'.format(
                    solid_selection=json.dumps(solid_selection)
                ),
            ],
        )

        assert result.exit_code == 0
        # Now that we have the snapshot make sure that it can be properly deserialized
        messages = list(ipc_read_event_stream(output_file))
        assert len(messages) == 1
        subset_result = messages[0]
        assert isinstance(subset_result, ExternalPipelineSubsetResult)
        assert subset_result.external_pipeline_data.name == 'foo'
        assert (
            len(
                subset_result.external_pipeline_data.pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps
            )
            == 1
        )


def test_execute_run_command():
    runner = CliRunner()

    with safe_tempfile_path() as filename:
        with seven.TemporaryDirectory() as temp_dir:
            instance = DagsterInstance.local_temp(temp_dir)
            pipeline_run = create_run_for_test(
                instance, pipeline_name='foo', environment_dict={}, mode='default',
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
                    '--pipeline-run-id={pipeline_run_id}'.format(
                        pipeline_run_id=pipeline_run.run_id
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


def test_partition_config_command():
    runner = CliRunner()

    with safe_tempfile_path() as filename:
        result = runner.invoke(
            partition_data_command,
            [
                '-y',
                file_relative_path(__file__, 'repository_file.yaml'),
                filename,
                '--partition-set-name',
                'baz_partitions',
                '--partition-name',
                'a',
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
