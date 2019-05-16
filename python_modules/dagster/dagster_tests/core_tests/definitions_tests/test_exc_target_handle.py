import imp
import importlib
import os

import pytest

from dagster import ExecutionTargetHandle, PipelineDefinition, RepositoryDefinition, lambda_solid

from dagster.core.definitions import LoaderEntrypoint
from dagster.core.definitions.exc_target_handle import (
    EPHEMERAL_NAME,
    _ExecutionTargetMode,
    _get_python_file_from_previous_stack_frame,
)
from dagster.core.errors import InvalidPipelineLoadingComboError
from dagster.utils import script_relative_path


def define_pipeline():
    return 1


def test_exc_target_handle():
    res = ExecutionTargetHandle.for_pipeline_fn(define_pipeline)
    assert res.data.python_file == __file__
    assert res.data.fn_name == 'define_pipeline'


def test_repository_python_file():
    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)

    exc_target_handle = ExecutionTargetHandle.for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'python_file': python_file, 'fn_name': 'define_bar_repo'}
    )
    assert exc_target_handle.mode == _ExecutionTargetMode.REPOSITORY
    assert exc_target_handle.entrypoint == LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo')
    assert exc_target_handle.data.pipeline_name == 'foo'

    with pytest.raises(InvalidPipelineLoadingComboError):
        ExecutionTargetHandle.for_pipeline_cli_args(
            {
                'module_name': 'kdjfkd',
                'pipeline_name': 'foo',
                'python_file': script_relative_path('bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': None,
            }
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        ExecutionTargetHandle.for_pipeline_cli_args(
            {
                'module_name': None,
                'pipeline_name': 'foo',
                'python_file': script_relative_path('bar_repo.py'),
                'fn_name': 'define_bar_repo',
                'repository_yaml': 'kjdfkdjf',
            }
        )


def test_repository_module():
    module = importlib.import_module('dagster')

    exc_target_handle = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'pipeline_name': 'foo',
            'python_file': None,
            'fn_name': 'define_bar_repo',
            'repository_yaml': None,
        }
    )
    assert exc_target_handle.mode == _ExecutionTargetMode.REPOSITORY
    assert exc_target_handle.entrypoint == LoaderEntrypoint(module, 'dagster', 'define_bar_repo')
    assert exc_target_handle.data.pipeline_name == 'foo'


def test_pipeline_python_file():
    python_file = script_relative_path('foo_pipeline.py')
    module = imp.load_source('foo_pipeline', python_file)

    exc_target_handle = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': None,
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': python_file,
            'repository_yaml': None,
        }
    )
    assert exc_target_handle.mode == _ExecutionTargetMode.PIPELINE
    assert exc_target_handle.entrypoint == LoaderEntrypoint(
        module, 'foo_pipeline', 'define_pipeline'
    )


def test_pipeline_module():
    exc_target_handle = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': 'dagster',
            'fn_name': 'define_pipeline',
            'pipeline_name': None,
            'python_file': None,
            'repository_yaml': None,
        }
    )
    assert exc_target_handle.mode == _ExecutionTargetMode.PIPELINE
    assert exc_target_handle.entrypoint == LoaderEntrypoint(
        importlib.import_module('dagster'), 'dagster', 'define_pipeline'
    )


def test_yaml_file():
    module = importlib.import_module('dagster.tutorials.intro_tutorial.repos')

    exc_target_handle = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': None,
            'pipeline_name': 'foobar',
            'python_file': None,
            'fn_name': None,
            'repository_yaml': script_relative_path('repository.yml'),
        }
    )
    assert exc_target_handle.mode == _ExecutionTargetMode.REPOSITORY
    assert exc_target_handle.entrypoint == LoaderEntrypoint(
        module, 'dagster.tutorials.intro_tutorial.repos', 'define_repo'
    )
    assert exc_target_handle.data.pipeline_name == 'foobar'

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert ExecutionTargetHandle.for_pipeline_cli_args(
            {'module_name': 'kdjfdk', 'pipeline_name': 'foobar'}
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert ExecutionTargetHandle.for_pipeline_cli_args(
            {'fn_name': 'kjdfkd', 'pipeline_name': 'foobar'}
        )

    with pytest.raises(InvalidPipelineLoadingComboError):
        assert ExecutionTargetHandle.for_pipeline_cli_args(
            {'pipeline_name': 'foobar', 'python_file': 'kjdfkdj'}
        )


def test_load_from_repository_file():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'pipeline_name': 'foo',
            'python_file': script_relative_path('test_exc_target_handle.py'),
            'fn_name': 'define_bar_repo',
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_repository_module():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': 'dagster.tutorials.intro_tutorial.repos',
            'pipeline_name': 'repo_demo_pipeline',
            'fn_name': 'define_repo',
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_load_from_pipeline_file():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'fn_name': 'define_foo_pipeline',
            'python_file': script_relative_path('test_exc_target_handle.py'),
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_load_from_pipeline_module():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'module_name': 'dagster.tutorials.intro_tutorial.repos',
            'fn_name': 'define_repo_demo_pipeline',
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_module_yaml():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {
            'pipeline_name': 'repo_demo_pipeline',
            'repository_yaml': script_relative_path('repository_module.yml'),
        }
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'repo_demo_pipeline'


def test_loader_from_default_repository_file_yaml():
    pipeline = ExecutionTargetHandle.for_pipeline_cli_args(
        {'pipeline_name': 'foo', 'repository_yaml': script_relative_path('repository_file.yml')}
    ).build_pipeline_definition()

    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == 'foo'


def test_repo_entrypoints():
    module = importlib.import_module('dagster.tutorials.intro_tutorial.repos')
    assert ExecutionTargetHandle.for_repo_yaml(
        script_relative_path('repository.yml')
    ).entrypoint == LoaderEntrypoint(
        module, 'dagster.tutorials.intro_tutorial.repos', 'define_repo'
    )

    module = importlib.import_module('dagster')
    assert ExecutionTargetHandle.for_repo_module(
        module_name='dagster', fn_name='define_bar_repo'
    ).entrypoint == LoaderEntrypoint(module, 'dagster', 'define_bar_repo')

    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)
    assert ExecutionTargetHandle.for_repo_python_file(
        python_file=python_file, fn_name='define_bar_repo'
    ).entrypoint == LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo')


def test_repo_yaml_module_dynamic_load():
    repository = ExecutionTargetHandle.for_repo_yaml(
        repository_yaml=script_relative_path('repository_module.yml')
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'demo_repository'


def test_repo_yaml_file_dynamic_load():
    repository = ExecutionTargetHandle.for_repo_yaml(
        repository_yaml=script_relative_path('repository_file.yml')
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load():
    repository = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster.tutorials.intro_tutorial.repos', fn_name='define_repo_demo_pipeline'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == EPHEMERAL_NAME


def test_repo_file_dynamic_load():
    repository = ExecutionTargetHandle.for_repo_python_file(
        python_file=script_relative_path('test_exc_target_handle.py'), fn_name='define_bar_repo'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load_from_pipeline():
    repository = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster.tutorials.intro_tutorial.repos', fn_name='define_repo_demo_pipeline'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('repo_demo_pipeline').name == 'repo_demo_pipeline'


def test_repo_file_dynamic_load_from_pipeline():
    repository = ExecutionTargetHandle.for_pipeline_python_file(
        python_file=script_relative_path('test_exc_target_handle.py'), fn_name='define_foo_pipeline'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == EPHEMERAL_NAME
    assert repository.get_pipeline('foo').name == 'foo'


@lambda_solid
def do_something():
    return 1


def define_foo_pipeline():
    return PipelineDefinition(name='foo', solids=[do_something])


def define_bar_repo():
    return RepositoryDefinition('bar', {'foo': define_foo_pipeline})


def test_get_python_file_from_previous_stack_frame():
    def nest_fn_call():
        # This ensures that `python_file` is this file
        python_file = _get_python_file_from_previous_stack_frame()
        return python_file

    # We check out dagster as 'workdir' in Buildkite, so we match the rest of the path to
    # python_modules/dagster/dagster_tests/core_tests/definitions_tests/test_exc_target_handle.py
    assert nest_fn_call().split(os.sep)[-6:] == [
        'python_modules',
        'dagster',
        'dagster_tests',
        'core_tests',
        'definitions_tests',
        'test_exc_target_handle.py',
    ]
