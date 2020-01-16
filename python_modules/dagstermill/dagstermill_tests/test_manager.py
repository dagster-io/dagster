import contextlib
import os
import pickle
import shutil
import tempfile
import threading
import uuid
from collections import OrderedDict

import dagstermill
import pytest
from dagstermill import DagstermillError
from dagstermill.manager import Manager

from dagster import (
    DagsterInvariantViolationError,
    Materialization,
    ModeDefinition,
    ResourceDefinition,
)
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.instance import DagsterInstance
from dagster.core.serdes import pack_value
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils import safe_tempfile_path


@contextlib.contextmanager
def in_pipeline_manager(
    pipeline_name='hello_world_pipeline',
    solid_handle=SolidHandle('hello_world', 'hello_world', None),
    handle_kwargs=None,
    mode=None,
    **kwargs
):
    manager = Manager()

    run_id = str(uuid.uuid4())
    instance = DagsterInstance.local_temp()
    marshal_dir = tempfile.mkdtemp()

    if not handle_kwargs:
        handle_kwargs = {
            'pipeline_name': pipeline_name,
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_world_pipeline',
        }

    pipeline_run_dict = pack_value(
        PipelineRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            mode=mode or 'default',
            environment_dict=None,
            selector=None,
            step_keys_to_execute=None,
            status=PipelineRunStatus.NOT_STARTED,
        )
    )

    try:
        with safe_tempfile_path() as output_log_file_path:
            context_dict = {
                'pipeline_run_dict': pipeline_run_dict,
                'solid_handle_kwargs': solid_handle._asdict(),
                'handle_kwargs': handle_kwargs,
                'marshal_dir': marshal_dir,
                'environment_dict': {},
                'output_log_path': output_log_file_path,
                'instance_ref_dict': pack_value(instance.get_ref()),
            }

            manager.reconstitute_pipeline_context(**dict(context_dict, **kwargs))
            yield manager
    finally:
        shutil.rmtree(marshal_dir)


def test_get_out_of_pipeline_context():
    context = dagstermill.get_context(
        mode_def=ModeDefinition(resource_defs={'list': ResourceDefinition(lambda _: [])})
    )

    assert context.pipeline_def.name == 'ephemeral_dagstermill_pipeline'
    assert context.resources.list == []


def test_get_out_of_pipeline_solid_config():
    assert dagstermill.get_context(solid_config='bar').solid_config == 'bar'


def test_out_of_pipeline_manager_yield_result():
    manager = Manager()
    assert manager.yield_result('foo') == 'foo'


def test_out_of_pipeline_manager_yield_complex_result():
    class Foo(object):
        pass

    manager = Manager()
    assert isinstance(manager.yield_result(Foo()), Foo)


def test_in_pipeline_manager_yield_bad_result():
    with in_pipeline_manager() as manager:
        with pytest.raises(
            DagstermillError, match='Solid hello_world does not have output named result'
        ):
            assert manager.yield_result('foo') == 'foo'


def test_yield_unserializable_result():
    manager = Manager()
    assert manager.yield_result(threading.Lock())

    with in_pipeline_manager(
        solid_handle=SolidHandle('hello_world_output', 'hello_world_output', None),
        handle_kwargs={
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_world_with_output_pipeline',
        },
    ) as manager:
        with pytest.raises(TypeError):
            manager.yield_result(threading.Lock())


def test_in_pipeline_manager_bad_solid():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=('Pipeline hello_world_pipeline has no solid named foobar'),
    ):
        with in_pipeline_manager(solid_handle=SolidHandle('foobar', 'foobar', None)) as _manager:
            pass


def test_in_pipeline_manager_bad_yield_result():
    with in_pipeline_manager() as manager:
        with pytest.raises(
            DagstermillError, match='Solid hello_world does not have output named result'
        ):
            manager.yield_result('foo')


def test_out_of_pipeline_yield_event():
    manager = Manager()
    assert manager.yield_event(Materialization('foo')) == Materialization('foo')


def test_in_pipeline_manager_resources():
    with in_pipeline_manager() as manager:
        assert manager.context.resources._asdict() == OrderedDict([])


def test_in_pipeline_manager_solid_config():
    with in_pipeline_manager() as manager:
        assert manager.context.solid_config is None

    with in_pipeline_manager(
        solid_handle=SolidHandle('hello_world_config', 'hello_world_config', None),
        handle_kwargs={
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_world_config_pipeline',
        },
    ) as manager:
        assert manager.context.solid_config == {'greeting': 'hello'}

    with in_pipeline_manager(
        solid_handle=SolidHandle('hello_world_config', 'hello_world_config', None),
        environment_dict={'solids': {'hello_world_config': {'config': {'greeting': 'bonjour'}}}},
        handle_kwargs={
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_world_config_pipeline',
        },
    ) as manager:
        assert manager.context.solid_config == {'greeting': 'bonjour'}


def test_in_pipeline_manager_with_resources():
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        with in_pipeline_manager(
            handle_kwargs={
                'pipeline_name': 'resource_pipeline',
                'fn_name': 'define_resource_pipeline',
                'module_name': 'dagstermill.examples.repository',
            },
            solid_handle=SolidHandle('hello_world_resource', 'hello_world_resource', None),
            environment_dict={'resources': {'list': {'config': path}}},
            mode='prod',
        ) as manager:
            assert len(manager.context.resources._asdict()) == 1

            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            assert len(messages) == 1
            assert messages[0][1] == 'Opened'

            manager.teardown_resources()

            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            assert len(messages) == 2
            assert messages[1][1] == 'Closed'

    finally:
        if os.path.exists(path):
            os.unlink(path)
