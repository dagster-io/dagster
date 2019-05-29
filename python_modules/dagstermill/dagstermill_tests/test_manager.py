import contextlib
import pickle
import shutil
import tempfile
import uuid

from collections import OrderedDict

import pytest

from dagster import Materialization

import dagstermill
from dagstermill import DagstermillError, Manager
from dagstermill.examples import define_example_repository
from dagstermill.serialize import SerializableRuntimeType


@contextlib.contextmanager
def in_pipeline_manager(register=True, **kwargs):
    repository_def = define_example_repository()

    manager = Manager()

    if register:
        manager.register_repository(repository_def)

    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            context_dict = dict(
                {
                    'run_id': run_id,
                    'mode': 'default',
                    'solid_def_name': 'hello_world',
                    'pipeline_def_name': 'hello_world_pipeline',
                    'marshal_dir': marshal_dir,
                    'environment_dict': {},
                    'output_log_path': output_log_file.name,
                    'input_name_type_dict': {},
                    'output_name_type_dict': {},
                },
                **kwargs
            )
            manager.populate_context(**context_dict)
            yield manager
    finally:
        shutil.rmtree(marshal_dir)


def test_get_out_of_pipeline_context():
    assert dagstermill.get_context().pipeline_def.name == 'Ephemeral Notebook Pipeline'


def test_out_of_pipeline_manager_yield_result():
    manager = Manager()
    assert manager.yield_result('foo') == 'foo'


def test_out_of_pipeline_manager_yield_complex_result():
    class Foo:
        pass

    manager = Manager()
    assert isinstance(manager.yield_result(Foo()), Foo)


def test_dummy_pipeline_manager_yield_bad_result():
    with in_pipeline_manager(register=False) as manager:
        with pytest.raises(
            DagstermillError, match='Solid hello_world does not have output named result'
        ):
            assert manager.yield_result('foo') == 'foo'


def test_dummy_manager_yield_complex_result():
    with in_pipeline_manager(
        register=False, output_name_type_dict={'result': SerializableRuntimeType.ANY}
    ) as manager:

        class Foo:
            pass

        with pytest.raises(DagstermillError, match='since it has a complex serialization format'):
            manager.yield_result(Foo())


def test_out_of_pipeline_manager_yield_materialization():
    manager = Manager()
    assert manager.yield_materialization('/path/to/artifact', 'artifact') == Materialization(
        '/path/to/artifact', 'artifact'
    )


def test_in_pipeline_manager_bad_yield_result():
    with in_pipeline_manager() as manager:
        with pytest.raises(
            DagstermillError, match='Solid hello_world does not have output named result'
        ):
            manager.yield_result('foo')


def test_in_notebook_manager_bad_load_parameter():
    class Foo:
        pass

    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            repository_def = define_example_repository()
            dagstermill.register_repository(repository_def)

            context_dict = {
                'run_id': run_id,
                'mode': 'default',
                'solid_def_name': 'hello_world',
                'pipeline_name': 'hello_world_pipeline',
                'marshal_dir': marshal_dir,
                'environment_config': {},
                'output_log_path': output_log_file.name,
                'input_name_type_dict': {},
                'output_name_type_dict': {},
            }
            dagstermill.populate_context(context_dict)

            with pytest.raises(KeyError):
                dagstermill.load_parameter('garble', Foo())
    finally:
        shutil.rmtree(marshal_dir)


def test_in_notebook_manager_bad_complex_load_parameter():

    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            dagstermill.deregister_repository()

            context_dict = {
                'run_id': run_id,
                'mode': 'default',
                'solid_def_name': 'hello_world',
                'pipeline_name': 'hello_world_pipeline',
                'marshal_dir': marshal_dir,
                'environment_config': {},
                'output_log_path': output_log_file.name,
                'input_name_type_dict': {'a': SerializableRuntimeType.NONE},
                'output_name_type_dict': {},
            }
            with pytest.raises(
                DagstermillError,
                match=(
                    'If Dagstermill solids have inputs that require serialization strategies that '
                ),
            ):
                dagstermill.populate_context(context_dict)

    finally:
        shutil.rmtree(marshal_dir)


def test_in_notebook_manager_load_parameter():
    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            repository_def = define_example_repository()
            dagstermill.register_repository(repository_def)

            context_dict = {
                'run_id': run_id,
                'mode': 'default',
                'solid_def_name': 'add_two_numbers',
                'pipeline_name': 'test_add_pipeline',
                'marshal_dir': marshal_dir,
                'environment_config': {},
                'output_log_path': output_log_file.name,
                'input_name_type_dict': {},
                'output_name_type_dict': {},
            }
            dagstermill.populate_context(context_dict)

            dagstermill.load_parameter('a', 7)

    finally:
        shutil.rmtree(marshal_dir)


def test_in_notebook_manager_load_parameter_pickleable():
    run_id = str(uuid.uuid4())

    marshal_dir = tempfile.mkdtemp()

    dagstermill.deregister_repository()

    try:
        with tempfile.NamedTemporaryFile() as output_log_file:
            with tempfile.NamedTemporaryFile() as pickle_file:
                pickle.dump(7, pickle_file)
                pickle_file.seek(0)

                context_dict = {
                    'run_id': run_id,
                    'mode': 'default',
                    'solid_def_name': 'add_two_numbers',
                    'pipeline_name': 'test_add_pipeline',
                    'marshal_dir': marshal_dir,
                    'environment_config': {},
                    'output_log_path': output_log_file.name,
                    'input_name_type_dict': {
                        'a': SerializableRuntimeType.PICKLE_SERIALIZABLE,
                        'b': SerializableRuntimeType.ANY,
                    },
                    'output_name_type_dict': {},
                }
                dagstermill.populate_context(context_dict)

                dagstermill.load_parameter('a', pickle_file.name)

                with pytest.raises(
                    DagstermillError, match='loading parameter b resulted in an error'
                ):
                    dagstermill.load_parameter('b', 9)

    finally:
        shutil.rmtree(marshal_dir)


def test_in_pipeline_manager_resources():
    with in_pipeline_manager() as manager:
        assert manager.context.resources._asdict() == OrderedDict([])
