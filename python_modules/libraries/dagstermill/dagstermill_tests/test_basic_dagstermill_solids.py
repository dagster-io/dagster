import os
import pickle
import tempfile
from contextlib import contextmanager

import nbformat
import pytest
from jupyter_client.kernelspec import NoSuchKernel
from nbconvert.preprocessors import ExecutePreprocessor
from papermill import PapermillExecutionError

from dagster import RunConfig, execute_pipeline
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.definitions.events import PathMetadataEntryData
from dagster.core.instance import DagsterInstance
from dagster.utils import safe_tempfile_path


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataEntryData):
            return metadata_entry.entry_data.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'
    ]
    for materialization_event in materialization_events:
        result_path = get_path(materialization_event)
        if os.path.exists(result_path):
            os.unlink(result_path)


@contextmanager
def exec_for_test(fn_name, env=None, raise_on_error=True, **kwargs):
    result = None

    handle = handle_for_pipeline_cli_args(
        {'module_name': 'dagstermill.examples.repository', 'fn_name': fn_name}
    )

    pipeline = handle.build_pipeline_definition()

    try:
        result = execute_pipeline(
            pipeline,
            env,
            instance=DagsterInstance.local_temp(),
            raise_on_error=raise_on_error,
            **kwargs
        )
        yield result
    finally:
        if result:
            cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_hello_world():
    with exec_for_test('define_hello_world_pipeline') as result:
        assert result.success


@pytest.mark.notebook_test
def test_reexecute_result_notebook():
    with exec_for_test('define_hello_world_pipeline') as result:
        assert result.success

        materialization_events = [
            x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'
        ]
        for materialization_event in materialization_events:
            result_path = get_path(materialization_event)

        if result_path.endswith('.ipynb'):
            with open(result_path) as fd:
                nb = nbformat.read(fd, as_version=4)
            ep = ExecutePreprocessor()
            ep.preprocess(nb, {})
            with open(result_path) as fd:
                assert nbformat.read(fd, as_version=4) == nb


@pytest.mark.notebook_test
def test_hello_world_with_output():
    with exec_for_test('define_hello_world_with_output_pipeline') as result:
        assert result.success
        assert result.result_for_solid('hello_world_output').output_value() == 'hello, world'


@pytest.mark.notebook_test
def test_hello_world_explicit_yield():
    with exec_for_test('define_hello_world_explicit_yield_pipeline') as result:
        materializations = [
            x for x in result.event_list if x.event_type_value == 'STEP_MATERIALIZATION'
        ]
        assert len(materializations) == 2
        assert get_path(materializations[0]).startswith('/tmp/dagstermill/')
        assert get_path(materializations[1]) == '/path/to/file'


@pytest.mark.notebook_test
def test_add_pipeline():
    with exec_for_test(
        'define_add_pipeline', {'loggers': {'console': {'config': {'log_level': 'ERROR'}}}}
    ) as result:
        assert result.success
        assert result.result_for_solid('add_two_numbers').output_value() == 3


@pytest.mark.notebook_test
def test_notebook_dag():
    with exec_for_test(
        'define_test_notebook_dag_pipeline',
        {'solids': {'load_a': {'config': 1}, 'load_b': {'config': 2}}},
    ) as result:
        assert result.success
        assert result.result_for_solid('add_two').output_value() == 3
        assert result.result_for_solid('mult_two').output_value() == 6


@pytest.mark.notebook_test
def test_error_notebook():
    with pytest.raises(PapermillExecutionError) as exc:
        with exec_for_test('define_error_pipeline') as result:
            pass

    assert 'Someone set up us the bomb' in str(exc.value)

    with exec_for_test('define_error_pipeline', raise_on_error=False) as result:
        assert not result.success
        assert result.step_event_list[1].event_type.value == 'STEP_MATERIALIZATION'
        assert result.step_event_list[2].event_type.value == 'STEP_FAILURE'


@pytest.mark.nettest
@pytest.mark.notebook_test
def test_tutorial_pipeline():
    with exec_for_test(
        'define_tutorial_pipeline', {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}}
    ) as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_reexecution():
    with exec_for_test('define_hello_world_pipeline') as result:
        assert result.success

        output_notebook_path = get_path(
            [x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'][0]
        )

        with tempfile.NamedTemporaryFile('w+', suffix='.py') as reexecution_notebook_file:
            reexecution_notebook_file.write(
                (
                    'from dagster import PipelineDefinition\n'
                    'from dagstermill import define_dagstermill_solid\n\n\n'
                    'reexecution_solid = define_dagstermill_solid(\n'
                    '    \'hello_world_reexecution\', \'{output_notebook_path}\'\n'
                    ')\n\n'
                    'def define_reexecution_pipeline():\n'
                    '    return PipelineDefinition([reexecution_solid])\n'
                ).format(output_notebook_path=output_notebook_path)
            )
            reexecution_notebook_file.flush()

            result = None

            handle = handle_for_pipeline_cli_args(
                {
                    'python_file': reexecution_notebook_file.name,
                    'fn_name': 'define_reexecution_pipeline',
                }
            )

            pipeline = handle.build_pipeline_definition()

            try:
                reexecution_result = execute_pipeline(
                    pipeline, instance=DagsterInstance.local_temp()
                )
                assert reexecution_result.success
            finally:
                if reexecution_result:
                    cleanup_result_notebook(reexecution_result)


@pytest.mark.notebook_test
def test_resources_notebook():
    with safe_tempfile_path() as path:
        with exec_for_test(
            'define_resource_pipeline',
            {'resources': {'list': {'config': path}}},
            run_config=RunConfig(mode='prod'),
        ) as result:
            assert result.success

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == 'Opened'
            assert msgs[4] == msgs[5] == 'Closed'
            assert msgs[1] == 'Hello, solid!'
            assert msgs[3] == 'Hello, notebook!'


@pytest.mark.notebook_test
def test_resources_notebook_with_exception():
    result = None
    with safe_tempfile_path() as path:
        with exec_for_test(
            'define_resource_with_exception_pipeline',
            {'resources': {'list': {'config': path}}},
            raise_on_error=False,
        ) as result:
            assert not result.success
            assert result.step_event_list[6].event_type.value == 'STEP_FAILURE'
            assert (
                'raise Exception()' in result.step_event_list[6].event_specific_data.error.message
            )

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == 'Opened'
            assert msgs[4] == msgs[5] == 'Closed'
            assert msgs[1] == 'Hello, solid!'
            assert msgs[3] == 'Hello, notebook!'


@pytest.mark.notebook_test
def test_bad_kernel():
    with pytest.raises(NoSuchKernel):
        with exec_for_test('define_bad_kernel_pipeline'):
            pass
