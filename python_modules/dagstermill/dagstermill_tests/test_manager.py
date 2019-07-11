import contextlib
import os
import pickle
import shutil
import tempfile
import threading
import uuid

from collections import OrderedDict

import pytest

import dagstermill

from dagster import (
    DagsterInvariantViolationError,
    Materialization,
    ModeDefinition,
    ResourceDefinition,
    RunConfig,
)
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.definitions.dependency import SolidHandle
from dagstermill import DagstermillError
from dagstermill.manager import Manager


@contextlib.contextmanager
def in_pipeline_manager(
    pipeline_name='hello_world_pipeline',
    solid_handle=SolidHandle('hello_world', 'hello_world', None),
    **kwargs
):
    manager = Manager()

    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    handle = handle_for_pipeline_cli_args(
        {
            'pipeline_name': pipeline_name,
            'module_name': 'dagstermill.examples.repository',
            'fn_name': 'define_hello_world_pipeline',
        }
    )

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            context_dict = {
                'run_config': RunConfig(run_id=run_id, mode='default'),
                'solid_handle': solid_handle,
                'handle': handle,
                'marshal_dir': marshal_dir,
                'environment_dict': {},
                'output_log_path': output_log_file.name,
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
    class Foo:
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
        handle=handle_for_pipeline_cli_args(
            {
                'module_name': 'dagstermill.examples.repository',
                'fn_name': 'define_hello_world_with_output_pipeline',
            }
        ),
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
        handle=handle_for_pipeline_cli_args(
            {
                'module_name': 'dagstermill.examples.repository',
                'fn_name': 'define_hello_world_config_pipeline',
            }
        ),
    ) as manager:
        assert manager.context.solid_config == {'greeting': 'hello'}

    with in_pipeline_manager(
        solid_handle=SolidHandle('hello_world_config', 'hello_world_config', None),
        environment_dict={'solids': {'hello_world_config': {'config': {'greeting': 'bonjour'}}}},
        handle=handle_for_pipeline_cli_args(
            {
                'module_name': 'dagstermill.examples.repository',
                'fn_name': 'define_hello_world_config_pipeline',
            }
        ),
    ) as manager:
        assert manager.context.solid_config == {'greeting': 'bonjour'}


def test_in_pipeline_manager_with_resources():
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        with in_pipeline_manager(
            handle=handle_for_pipeline_cli_args(
                {
                    'pipeline_name': 'resource_pipeline',
                    'fn_name': 'define_resource_pipeline',
                    'module_name': 'dagstermill.examples.repository',
                }
            ),
            solid_handle=SolidHandle('hello_world_resource', 'hello_world_resource', None),
            environment_dict={'resources': {'list': {'config': path}}},
            run_config=RunConfig(mode='prod'),
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
