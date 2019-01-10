from collections import defaultdict

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    lambda_solid,
)


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

    assert set(['foo', 'bar']) == set([pipeline.name for pipeline in pipelines])

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

    with pytest.raises(DagsterInvalidDefinitionError):
        repo.get_all_pipelines()


def test_dupe_solid_repo_definition_unforced():
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
        enforce_uniqueness=False,
    )

    assert repo.get_all_pipelines()

    with pytest.raises(DagsterInvariantViolationError):
        repo.get_solid_def('first')
