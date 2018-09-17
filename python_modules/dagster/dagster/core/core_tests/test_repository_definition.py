from collections import defaultdict

from dagster import (
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
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
        ]
    )


def test_repo_definition():
    called = defaultdict(int)
    repo = RepositoryDefinition(
        name='some_repo',
        pipeline_dict={
            'foo': lambda: create_single_node_pipeline('foo', called),
            'bar': lambda: create_single_node_pipeline('bar', called),
        }
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
