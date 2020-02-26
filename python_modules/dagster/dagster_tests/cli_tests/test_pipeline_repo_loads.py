import importlib

import pytest

from dagster.cli.load_handle import UsageError, handle_for_pipeline_cli_args
from dagster.core.definitions import (
    ExecutionTargetHandle,
    LoaderEntrypoint,
    PipelineDefinition,
    RepositoryDefinition,
)
from dagster.core.definitions.decorators import lambda_solid
from dagster.core.definitions.handle import _ExecutionTargetMode
from dagster.seven import import_module_from_path
from dagster.utils import file_relative_path


def test_repository_python_file():
    python_file = file_relative_path(__file__, 'bar_repo.py')
    module = import_module_from_path('bar_repo', python_file)

    handle = handle_for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'python_file': python_file, 'fn_name': 'define_bar_repo'}
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    assert handle.entrypoint == LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo', handle)
    assert handle.data.pipeline_name == 'foo'
    assert handle.entrypoint.from_handle == handle

    with pytest.raises(UsageError):
        handle_for_pipeline_cli_args(
            {
                'module_name': 'kdjfkd',
                'pipeline_name': 'foo',
                'python_file': file_relative_path(__file__, 'bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': None,
            }
        )

    with pytest.raises(UsageError):
        handle_for_pipeline_cli_args(
            {
                'module_name': None,
                'pipeline_name': 'foo',
                'python_file': file_relative_path(__file__, 'bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': 'kjdfkdjf',
            }
        )


def test_repository_module():
    module = importlib.import_module('dagster')

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'pipeline_name': 'foo',
            'python_file': None,
            'fn_name': 'define_bar_repo',
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    expected = LoaderEntrypoint(module, 'dagster', 'define_bar_repo')
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle
    assert handle.data.pipeline_name == 'foo'


def test_pipeline_python_file():
    python_file = file_relative_path(__file__, 'foo_pipeline.py')
    module = import_module_from_path('foo_pipeline', python_file)

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': None,
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': python_file,
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    expected = LoaderEntrypoint(module, 'foo_pipeline', 'define_pipeline')
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle


def test_pipeline_module():
    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': None,
            'repository_yaml': None,
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE
    expected = LoaderEntrypoint(importlib.import_module('dagster'), 'dagster', 'define_pipeline')
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle


def test_yaml_file():
    module = importlib.import_module('dagster_examples.intro_tutorial.repos')

    handle = handle_for_pipeline_cli_args(
        {
            'module_name': None,
            'pipeline_name': 'foobar',
            'python_file': None,
            'fn_name': None,
            'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
        }
    )
    assert handle.mode == _ExecutionTargetMode.PIPELINE

    expected = LoaderEntrypoint(module, 'dagster_examples.intro_tutorial.repos', 'define_repo')
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name

    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle

    assert handle.data.pipeline_name == 'foobar'

    with pytest.raises(UsageError):
        assert handle_for_pipeline_cli_args({'module_name': 'kdjfdk', 'pipeline_name': 'foobar'})

    with pytest.raises(UsageError):
        assert handle_for_pipeline_cli_args({'fn_name': 'kjdfkd', 'pipeline_name': 'foobar'})

    with pytest.raises(UsageError):
        assert handle_for_pipeline_cli_args({'pipeline_name': 'foobar', 'python_file': 'kjdfkdj'})


def test_load_from_repository_file():
    handle = handle_for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'python_file': __file__, 'fn_name': 'define_bar_repo'}
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'

    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def test_load_from_repository_module():
    handle = handle_for_pipeline_cli_args(
        {
            'module_name': 'dagster_examples.intro_tutorial.repos',
            'pipeline_name': 'hello_cereal_pipeline',
            'fn_name': 'define_repo',
        }
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'hello_cereal_pipeline'
    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def test_load_from_pipeline_file():
    handle = handle_for_pipeline_cli_args(
        {'fn_name': 'define_foo_pipeline', 'python_file': __file__}
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'
    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def test_load_from_pipeline_module():
    handle = handle_for_pipeline_cli_args(
        {'module_name': 'dagster_examples.intro_tutorial.repos', 'fn_name': 'hello_cereal_pipeline'}
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'hello_cereal_pipeline'
    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def test_loader_from_default_repository_module_yaml():
    handle = handle_for_pipeline_cli_args(
        {
            'pipeline_name': 'hello_cereal_pipeline',
            'repository_yaml': file_relative_path(__file__, 'repository_module.yaml'),
        }
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'hello_cereal_pipeline'
    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def test_loader_from_default_repository_file_yaml():
    handle = handle_for_pipeline_cli_args(
        {
            'pipeline_name': 'foo',
            'repository_yaml': file_relative_path(__file__, 'repository_file.yaml'),
        }
    )
    pipeline = handle.build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'
    assert ExecutionTargetHandle.get_handle(pipeline) == (handle, None)


def define_foo_pipeline():
    @lambda_solid
    def do_something():
        return 1

    return PipelineDefinition(name='foo', solid_defs=[do_something])


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})
