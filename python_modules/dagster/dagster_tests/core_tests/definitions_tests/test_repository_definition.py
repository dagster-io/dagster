from collections import defaultdict

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    lambda_solid,
    solid,
    Field,
    Bool,
    Dict,
    execute_pipeline,
    DagsterExecutionStepExecutionError,
)
from dagster.utils import script_relative_path


def create_single_node_pipeline(name, called):
    called[name] = called[name] + 1
    return PipelineDefinition(
        name=name,
        solids=[
            SolidDefinition(
                name=name + '_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args, **_kwargs: None,
            )
        ],
    )


def test_repo_definition():
    called = defaultdict(int)
    repo = RepositoryDefinition(
        name='some_repo',
        pipeline_dict={
            'foo': lambda: create_single_node_pipeline('foo', called),
            'bar': lambda: create_single_node_pipeline('bar', called),
        },
    )

    foo_pipeline = repo.get_pipeline('foo')
    assert isinstance(foo_pipeline, PipelineDefinition)
    assert foo_pipeline.name == 'foo'

    assert 'foo' in called
    assert called['foo'] == 1
    assert 'bar' not in called

    bar_pipeline = repo.get_pipeline('bar')
    assert isinstance(bar_pipeline, PipelineDefinition)
    assert bar_pipeline.name == 'bar'

    assert 'foo' in called
    assert called['foo'] == 1
    assert 'bar' in called
    assert called['bar'] == 1

    foo_pipeline = repo.get_pipeline('foo')
    assert isinstance(foo_pipeline, PipelineDefinition)
    assert foo_pipeline.name == 'foo'

    assert 'foo' in called
    assert called['foo'] == 1

    pipelines = repo.get_all_pipelines()

    assert set(['foo', 'bar']) == {pipeline.name for pipeline in pipelines}

    assert repo.get_solid_def('foo_solid').name == 'foo_solid'
    assert repo.get_solid_def('bar_solid').name == 'bar_solid'


def test_dupe_solid_repo_definition():
    @lambda_solid(name='same')
    def noop():
        pass

    @lambda_solid(name='same')
    def noop2():
        pass

    repo = RepositoryDefinition(
        'error_repo',
        pipeline_dict={
            'first': lambda: PipelineDefinition(name='first', solids=[noop]),
            'second': lambda: PipelineDefinition(name='second', solids=[noop2]),
        },
    )

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        repo.get_all_pipelines()

    assert str(exc_info.value) == (
        'You have defined two solids named "same" in repository "error_repo". '
        'Solid names must be unique within a repository. The solid has been defined '
        'in pipeline "first" and it has been defined again in pipeline "second."'
    )


def test_dupe_solid_repo_definition_error_opt_out():
    @lambda_solid(name='same')
    def noop():
        pass

    @lambda_solid(name='same')
    def noop2():
        pass

    repo = RepositoryDefinition(
        'skip_error_repo',
        pipeline_dict={
            'first': lambda: PipelineDefinition(name='first', solids=[noop]),
            'second': lambda: PipelineDefinition(name='second', solids=[noop2]),
        },
        enforce_solid_def_uniqueness=False,
    )

    assert repo.get_all_pipelines()

    with pytest.raises(DagsterInvariantViolationError):
        repo.get_solid_def('foo')


def test_repo_config():
    @solid(config_field=Field(Dict(fields={'error': Field(Bool)})))
    def can_fail(context):
        if context.solid_config['error']:
            raise Exception('I did an error')
        return 'cool'

    @lambda_solid
    def always_fail():
        raise Exception('I always do this')

    repo = RepositoryDefinition(
        'config_test',
        pipeline_dict={
            'simple': lambda: PipelineDefinition(name='simple', solids=[can_fail, always_fail])
        },
        repo_config={
            'pipelines': {
                'simple': {
                    'presets': {
                        'passing': {
                            'environment_files': [script_relative_path('pass_env.yml')],
                            'solid_subset': ['can_fail'],
                        },
                        'failing_1': {
                            'environment_files': [script_relative_path('fail_env.yml')],
                            'solid_subset': ['can_fail'],
                        },
                        'failing_2': {'environment_files': [script_relative_path('pass_env.yml')]},
                        'invalid_1': {
                            'environment_files': [script_relative_path('not_a_file.yml')]
                        },
                        'invalid_2': {
                            'environment_files': [
                                script_relative_path('test_repository_definition.py')
                            ]
                        },
                    }
                }
            }
        },
    )

    execute_pipeline(**repo.get_preset_pipeline('simple', 'passing'))

    with pytest.raises(DagsterExecutionStepExecutionError):
        execute_pipeline(**repo.get_preset_pipeline('simple', 'failing_1'))

    with pytest.raises(DagsterExecutionStepExecutionError):
        execute_pipeline(**repo.get_preset_pipeline('simple', 'failing_2'))

    with pytest.raises(DagsterInvalidDefinitionError, match="not_a_file.yml"):
        execute_pipeline(**repo.get_preset_pipeline('simple', 'invalid_1'))

    with pytest.raises(DagsterInvariantViolationError, match="error attempting to parse yaml"):
        execute_pipeline(**repo.get_preset_pipeline('simple', 'invalid_2'))

    with pytest.raises(DagsterInvariantViolationError, match="Could not find pipeline"):
        execute_pipeline(**repo.get_preset_pipeline('not_real', 'passing'))

    with pytest.raises(DagsterInvariantViolationError, match="Could not find preset"):
        execute_pipeline(**repo.get_preset_pipeline('simple', 'not_failing'))
