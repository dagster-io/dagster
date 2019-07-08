from collections import defaultdict

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    lambda_solid,
)


def create_single_node_pipeline(name, called):
    called[name] = called[name] + 1
    return PipelineDefinition(
        name=name,
        solid_defs=[
            SolidDefinition(
                name=name + '_solid',
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args, **_kwargs: None,
            )
        ],
    )


def test_repo_lazy_definition():
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

    assert repo.solid_def_named('foo_solid').name == 'foo_solid'
    assert repo.solid_def_named('bar_solid').name == 'bar_solid'


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
            'first': lambda: PipelineDefinition(name='first', solid_defs=[noop]),
            'second': lambda: PipelineDefinition(name='second', solid_defs=[noop2]),
        },
    )

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        repo.get_all_pipelines()

    assert str(exc_info.value) == (
        'You have defined two solid definitions named "same" in repository '
        '"error_repo". Solid definition names must be unique within a '
        'repository. The solid definition has been defined '
        'in pipeline "first" and it has been defined again '
        'in pipeline "second."'
    )


def test_non_lazy_pipeline_dict():
    called = defaultdict(int)
    repo = RepositoryDefinition(
        name='some_repo',
        pipeline_defs=[
            create_single_node_pipeline('foo', called),
            create_single_node_pipeline('bar', called),
        ],
    )

    assert repo.get_pipeline('foo').name == 'foo'
    assert repo.get_pipeline('bar').name == 'bar'


def test_conflict():
    called = defaultdict(int)
    with pytest.raises(Exception, match='Duplicate pipelines named foo'):
        RepositoryDefinition(
            name='some_repo',
            pipeline_defs=[create_single_node_pipeline('foo', called)],
            pipeline_dict={'foo': lambda: create_single_node_pipeline('foo', called)},
        )


def test_key_mismatch():
    called = defaultdict(int)
    repo = RepositoryDefinition(
        name='some_repo', pipeline_dict={'foo': lambda: create_single_node_pipeline('bar', called)}
    )
    with pytest.raises(Exception, match='Name does not match'):
        repo.get_pipeline('foo')
