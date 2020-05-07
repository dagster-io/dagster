import json
import os
import tempfile
from uuid import uuid4

from click.testing import CliRunner

from dagster import file_relative_path
from dagster.cli.api import (
    execute_pipeline_command,
    pipeline_snapshot_command,
    repository_snapshot_command,
)
from dagster.core.events import DagsterEventType
from dagster.core.host_representation import ExternalPipelineData, ExternalRepositoryData
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import IPCEndMessage, IPCStartMessage, ipc_read_event_stream
from dagster.seven.temp_dir import get_system_temp_directory
from dagster.utils.temp_file import get_temp_dir


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


def test_execute_pipeline_command():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile() as f:
        result = runner.invoke(
            execute_pipeline_command,
            [
                '-y',
                file_relative_path(__file__, 'repository_file.yaml'),
                'foo',
                f.name,
                '--environment-dict={}',
                '--mode=default',
            ],
        )

        assert result.exit_code == 0

        # Read lines from output file, and strip newline characters
        lines = [line.decode('utf-8').rstrip() for line in f.readlines()]
        assert len(lines) == 13

        # Check all lines are serialized dagster named tuples
        for line in lines:
            deserialize_json_to_dagster_namedtuple(line)

        # Check for start ane dnd messages
        assert deserialize_json_to_dagster_namedtuple(lines[0]) == IPCStartMessage()
        assert deserialize_json_to_dagster_namedtuple(lines[-1]) == IPCEndMessage()


def test_execute_pipeline_command_missing_args():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile() as f:
        result = runner.invoke(
            execute_pipeline_command,
            ['-y', file_relative_path(__file__, 'repository_file.yaml'), 'foo', f.name],
        )

        assert result.exit_code == 0

        # Read lines from output file, and strip newline characters
        lines = [line.decode('utf-8').rstrip() for line in f.readlines()]
        assert len(lines) == 3

        # Check all lines are serialized dagster named tuples
        for line in lines:
            deserialize_json_to_dagster_namedtuple(line)

        # Check for start ane dnd messages
        assert deserialize_json_to_dagster_namedtuple(lines[0]) == IPCStartMessage()
        assert deserialize_json_to_dagster_namedtuple(lines[-1]) == IPCEndMessage()


def _execute_pipeline_command(
    repository_file, pipeline_name, environment_dict, mode=None, solid_subset=None
):
    with get_temp_dir(in_directory=get_system_temp_directory()) as tmp_dir:

        output_file_name = "{}.json".format(uuid4())
        output_file = os.path.join(tmp_dir, output_file_name)

        command = (
            "dagster api execute_pipeline -y {repository_file} {pipeline_name} "
            "{output_file} --environment-dict='{environment_dict}' --mode={mode}".format(
                repository_file=repository_file,
                pipeline_name=pipeline_name,
                output_file=output_file,
                environment_dict=json.dumps(environment_dict),
                mode=mode,
            )
        )

        if solid_subset:
            command += " --solid_subset={solid_subset}".format(solid_subset=",".join(solid_subset))

        os.popen(command)

        for message in ipc_read_event_stream(output_file):
            yield message


def test_execute_pipeline_with_ipc():
    events = []
    for event in _execute_pipeline_command(
        file_relative_path(__file__, 'repository_file.yaml'), 'foo', {}, 'default'
    ):
        print(event)
        events.append(event)

    assert len(events) == 11
    assert events[0].event_type_value == DagsterEventType.PIPELINE_START.value
    assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value
