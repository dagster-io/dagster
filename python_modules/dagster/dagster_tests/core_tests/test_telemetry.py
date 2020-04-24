import json
import os

import pytest
import yaml
from click.testing import CliRunner

from dagster import seven
from dagster.cli.pipeline import pipeline_execute_command
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import get_dir_from_dagster_home
from dagster.core.test_utils import environ
from dagster.utils import pushd, script_relative_path

EXPECTED_KEYS = set(
    ['action', 'client_time', 'elapsed_time', 'event_id', 'instance_id', 'metadata',]
)


def path_to_tutorial_file(path):
    return script_relative_path(
        os.path.join('../../../../examples/dagster_examples/intro_tutorial/', path)
    )


@pytest.mark.skipif(
    os.name == 'nt', reason="TemporaryDirectory disabled for win because of event.log contention"
)
def test_dagster_telemetry_enabled(caplog):
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            with open(os.path.join(temp_dir, 'dagster.yaml'), 'w') as fd:
                yaml.dump({'telemetry': {'enabled': True}}, fd, default_flow_style=False)

            DagsterInstance.local_temp(temp_dir)
            runner = CliRunner(env={'DAGSTER_HOME': temp_dir})
            with pushd(path_to_tutorial_file('')):
                result = runner.invoke(
                    pipeline_execute_command,
                    [
                        '-f',
                        path_to_tutorial_file('hello_cereal.py'),
                        '-n',
                        'hello_cereal_pipeline',
                    ],
                )

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 4
                assert result.exit_code == 0


@pytest.mark.skipif(
    os.name == 'nt', reason="TemporaryDirectory disabled for win because of event.log contention"
)
def test_dagster_telemetry_disabled(caplog):
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            with open(os.path.join(temp_dir, 'dagster.yaml'), 'w') as fd:
                yaml.dump({'telemetry': {'enabled': False}}, fd, default_flow_style=False)

            DagsterInstance.local_temp(temp_dir)

            runner = CliRunner(env={'DAGSTER_HOME': temp_dir})
            with pushd(path_to_tutorial_file('')):
                result = runner.invoke(
                    pipeline_execute_command,
                    [
                        '-f',
                        path_to_tutorial_file('hello_cereal.py'),
                        '-n',
                        'hello_cereal_pipeline',
                    ],
                )

            assert not os.path.exists(os.path.join(get_dir_from_dagster_home('logs'), 'event.log'))
            assert len(caplog.records) == 0
            assert result.exit_code == 0


@pytest.mark.skipif(
    os.name == 'nt', reason="TemporaryDirectory disabled for win because of event.log contention"
)
def test_dagster_telemetry_unset(caplog):
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            with open(os.path.join(temp_dir, 'dagster.yaml'), 'w') as fd:
                yaml.dump({}, fd, default_flow_style=False)

            DagsterInstance.local_temp(temp_dir)
            runner = CliRunner(env={'DAGSTER_HOME': temp_dir})
            with pushd(path_to_tutorial_file('')):
                result = runner.invoke(
                    pipeline_execute_command,
                    [
                        '-f',
                        path_to_tutorial_file('hello_cereal.py'),
                        '-n',
                        'hello_cereal_pipeline',
                    ],
                )

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 4
                assert result.exit_code == 0
