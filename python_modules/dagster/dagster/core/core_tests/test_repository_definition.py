from collections import defaultdict

from dagster import (
    ArgumentDefinition,
    LibraryDefinition,
    LibrarySolidDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    Result,
    SolidDefinition,
    types,
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


def create_library_solid_def():
    def get_t_fn(args):
        def _t_fn(*_args, **_kwargs):
            yield Result({args['key']: args['value']})

        return _t_fn

    return LibrarySolidDefinition(
        name='return_value_in_key',
        argument_def_dict={
            'key' : ArgumentDefinition(types.String),
            'value' : ArgumentDefinition(types.String),
        },
        solid_creation_fn=lambda name, args: SolidDefinition(
            name=name,
            inputs=[],
            outputs=[OutputDefinition()],
            transform_fn=get_t_fn(args),
        )
    )


def test_repo_with_libraries():
    called = defaultdict(int)
    repo = RepositoryDefinition(
        name='some_repo',
        pipeline_dict={
            'foo': lambda: create_single_node_pipeline('foo', called),
            'bar': lambda: create_single_node_pipeline('bar', called),
        },
        libraries=[
            LibraryDefinition(
                name='some_library',
                library_solids=[create_library_solid_def()],
            )
        ]
    )

    assert isinstance(repo, RepositoryDefinition)


def test_repo_def_errors():
    pass  # TODO
