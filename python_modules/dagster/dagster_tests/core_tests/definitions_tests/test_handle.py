import imp
import importlib
import os
import types

import pytest

from dagster import (
    DagsterInvariantViolationError,
    ExecutionTargetHandle,
    PipelineDefinition,
    RepositoryDefinition,
    check,
    lambda_solid,
    pipeline,
)
from dagster.core.definitions import LoaderEntrypoint
from dagster.core.definitions.handle import (
    EPHEMERAL_NAME,
    _ExecutionTargetHandleData,
    _get_python_file_from_previous_stack_frame,
)
from dagster.utils import script_relative_path

NOPE = 'this is not a pipeline or repo or callable'


@lambda_solid
def do_something():
    return 1


@pipeline
def foo_pipeline():
    return do_something()


def define_foo_pipeline():
    return foo_pipeline


def define_bar_repo():
    return RepositoryDefinition('bar', pipeline_defs=[foo_pipeline])


def define_not_a_pipeline_or_repo():
    return 'nope'


def test_exc_target_handle():
    res = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'foo_pipeline')
    assert os.path.abspath(res.data.python_file) == os.path.abspath(__file__)
    assert res.data.fn_name == 'foo_pipeline'

    res = ExecutionTargetHandle.from_dict(res.to_dict())
    assert os.path.abspath(res.data.python_file) == os.path.abspath(__file__)
    assert res.data.fn_name == 'foo_pipeline'


def test_loader_entrypoint():
    # Check missing entrypoint
    le = LoaderEntrypoint.from_file_target(__file__, 'doesnt_exist')
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        le.perform_load()

    assert "doesnt_exist not found in module <module 'test_handle'" in str(exc_info.value)

    # Check pipeline entrypoint
    le = LoaderEntrypoint.from_file_target(__file__, 'foo_pipeline')
    inst = le.perform_load()
    assert isinstance(inst, PipelineDefinition)
    assert inst.name == 'foo_pipeline'

    # Check repository / pipeline def function entrypoint
    le = LoaderEntrypoint.from_file_target(__file__, 'define_foo_pipeline')
    inst = le.perform_load()
    assert isinstance(inst, PipelineDefinition)
    assert inst.name == 'foo_pipeline'

    le = LoaderEntrypoint.from_file_target(__file__, 'define_bar_repo')
    inst = le.perform_load()
    assert isinstance(inst, RepositoryDefinition)
    assert inst.name == 'bar'

    le = LoaderEntrypoint.from_file_target(__file__, 'define_not_a_pipeline_or_repo')
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        inst = le.perform_load()
    assert (
        str(exc_info.value)
        == 'define_not_a_pipeline_or_repo is a function but must return a PipelineDefinition or a '
        'RepositoryDefinition, or be decorated with @pipeline.'
    )

    # Check failure case
    le = LoaderEntrypoint.from_file_target(__file__, 'NOPE')
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        inst = le.perform_load()
    assert (
        str(exc_info.value)
        == 'NOPE must be a function that returns a PipelineDefinition or a RepositoryDefinition, '
        'or a function decorated with @pipeline.'
    )

    # YAML
    le = LoaderEntrypoint.from_yaml(script_relative_path('repository.yaml'))
    assert isinstance(le.module, types.ModuleType)
    assert le.module.__name__ == 'dagster_examples.intro_tutorial.repos'
    assert le.module_name == 'dagster_examples.intro_tutorial.repos'

    inst = le.perform_load()
    assert isinstance(inst, RepositoryDefinition)


def test_repo_entrypoints():
    module = importlib.import_module('dagster_examples.intro_tutorial.repos')

    expected = LoaderEntrypoint(module, 'dagster_examples.intro_tutorial.repos', 'define_repo')
    handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('repository.yaml'))
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle

    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name

    module = importlib.import_module('dagster')
    expected = LoaderEntrypoint(module, 'dagster', 'define_bar_repo')
    handle = ExecutionTargetHandle.for_repo_module(module_name='dagster', fn_name='define_bar_repo')
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle

    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name

    python_file = script_relative_path('bar_repo.py')
    module = imp.load_source('bar_repo', python_file)

    expected = LoaderEntrypoint(module, 'bar_repo', 'define_bar_repo')
    handle = ExecutionTargetHandle.for_repo_python_file(
        python_file=python_file, fn_name='define_bar_repo'
    )
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name
    assert handle.entrypoint.from_handle == handle

    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    assert handle.entrypoint.module == expected.module
    assert handle.entrypoint.module_name == expected.module_name
    assert handle.entrypoint.fn_name == expected.fn_name


def test_for_repo_fn_with_pipeline_name():
    handle = ExecutionTargetHandle.for_repo_fn(define_bar_repo)
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())

    repo = handle.build_repository_definition()
    assert repo.name == 'bar'

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        handle.build_pipeline_definition()
    assert (
        str(exc_info.value) == 'Cannot construct a pipeline from a repository-based '
        'ExecutionTargetHandle without a pipeline name. Use with_pipeline_name() to construct a '
        'pipeline ExecutionTargetHandle.'
    )

    handle_for_pipeline = handle.with_pipeline_name('foo_pipeline')
    repo = handle_for_pipeline.build_repository_definition()
    assert repo.name == 'bar'

    pipe = handle_for_pipeline.build_pipeline_definition()
    assert pipe.name == 'foo_pipeline'

    handle_double = handle_for_pipeline.with_pipeline_name('foo_pipeline')
    pipe = handle_double.build_pipeline_definition()
    assert pipe.name == 'foo_pipeline'


def test_bad_modes():
    handle = ExecutionTargetHandle.for_repo_fn(define_bar_repo).with_pipeline_name('foo_pipeline')
    handle.mode = 'not a mode'

    with pytest.raises(check.CheckError) as exc_info:
        handle.entrypoint()
    assert str(exc_info.value) == 'Failure condition: Unhandled mode not a mode'

    with pytest.raises(check.CheckError) as exc_info:
        handle.build_pipeline_definition()
    assert str(exc_info.value) == 'Failure condition: Unhandled mode not a mode'

    with pytest.raises(check.CheckError) as exc_info:
        handle.build_repository_definition()
    assert str(exc_info.value) == 'Failure condition: Unhandled mode not a mode'


def test_exc_target_handle_data():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        _ExecutionTargetHandleData().get_repository_entrypoint()

    assert str(exc_info.value) == (
        'You have attempted to load a repository with an invalid combination of properties. '
        'repository_yaml None module_name None python_file None fn_name None.'
    )

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        _ExecutionTargetHandleData().get_pipeline_entrypoint()

    assert str(exc_info.value) == (
        'You have attempted to directly load a pipeline with an invalid combination of properties '
        'module_name None python_file None fn_name None.'
    )


def test_repo_yaml_module_dynamic_load():
    handle = ExecutionTargetHandle.for_repo_yaml(
        repository_yaml=script_relative_path('repository_module.yaml')
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'hello_cereal_repository'
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


def test_repo_yaml_file_dynamic_load():
    handle = ExecutionTargetHandle.for_repo_yaml(
        repository_yaml=script_relative_path('repository_file.yaml')
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


def test_repo_module_dynamic_load():
    handle = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster_examples.intro_tutorial.repos', fn_name='hello_cereal_pipeline'
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == EPHEMERAL_NAME
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


def test_repo_file_dynamic_load():
    handle = ExecutionTargetHandle.for_repo_python_file(
        python_file=script_relative_path('test_handle.py'), fn_name='define_bar_repo'
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == 'bar'
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


def test_repo_module_dynamic_load_from_pipeline():
    handle = ExecutionTargetHandle.for_pipeline_module(
        module_name='dagster_examples.intro_tutorial.repos', fn_name='hello_cereal_pipeline'
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == '<<unnamed>>'
    assert repository.get_pipeline('hello_cereal_pipeline').name == 'hello_cereal_pipeline'
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


def test_repo_file_dynamic_load_from_pipeline():
    handle = ExecutionTargetHandle.for_pipeline_python_file(
        python_file=script_relative_path('test_handle.py'), fn_name='foo_pipeline'
    )
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repository = handle.build_repository_definition()

    assert isinstance(repository, RepositoryDefinition)
    assert repository.name == EPHEMERAL_NAME
    assert repository.get_pipeline('foo_pipeline').name == 'foo_pipeline'
    assert ExecutionTargetHandle.get_handle(repository) == (handle, None)


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


def test_build_repository_definition():
    handle = ExecutionTargetHandle.for_repo_python_file(__file__, 'define_foo_pipeline')
    handle = ExecutionTargetHandle.from_dict(handle.to_dict())
    repo = handle.build_repository_definition()
    assert repo.name == EPHEMERAL_NAME
