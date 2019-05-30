import imp
import importlib
import os


from dagster import ExecutionTargetHandle, PipelineDefinition, RepositoryDefinition, lambda_solid

from dagster.core.definitions import LoaderEntrypoint
from dagster.core.definitions.handle import (
    EPHEMERAL_NAME,
    _get_python_file_from_previous_stack_frame,
)

from dagster.utils import script_relative_path


def define_pipeline():
    return 1


def test_exc_target_handle():
    res = ExecutionTargetHandle.for_pipeline_fn(define_pipeline)
    assert res.data.python_file == __file__
    assert res.data.fn_name == 'define_pipeline'


def test_repo_entrypoints():
    module = importlib.import_module('dagster_examples.intro_tutorial.repos')
    assert ExecutionTargetHandle.for_repo_yaml(
        script_relative_path('repository.yaml')
    ).entrypoint == LoaderEntrypoint(module, 'dagster_examples.intro_tutorial.repos', 'define_repo')

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
        repository_yaml=script_relative_path('repository_module.yaml')
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'demo_repository'


def test_repo_yaml_file_dynamic_load():
    repository = ExecutionTargetHandle.for_repo_yaml(
        repository_yaml=script_relative_path('repository_file.yaml')
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load():
    repository = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster_examples.intro_tutorial.repos', fn_name='define_repo_demo_pipeline'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == EPHEMERAL_NAME


def test_repo_file_dynamic_load():
    repository = ExecutionTargetHandle.for_repo_python_file(
        python_file=script_relative_path('test_handle.py'), fn_name='define_bar_repo'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'


def test_repo_module_dynamic_load_from_pipeline():
    repository = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster_examples.intro_tutorial.repos', fn_name='define_repo_demo_pipeline'
    ).build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('repo_demo_pipeline').name == 'repo_demo_pipeline'


def test_repo_file_dynamic_load_from_pipeline():
    repository = ExecutionTargetHandle.for_pipeline_python_file(
        python_file=script_relative_path('test_handle.py'), fn_name='define_foo_pipeline'
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
    # python_modules/dagster/dagster_tests/core_tests/definitions_tests/test_handle.py
    assert nest_fn_call().split(os.sep)[-6:] == [
        'python_modules',
        'dagster',
        'dagster_tests',
        'core_tests',
        'definitions_tests',
        'test_handle.py',
    ]
