import dagster
from dagster.core.definitions import InputDefinition
from dagster.core.decorators import solid


@solid()
def step_one_no_external_source():
    return {'foo': 'bar'}


@solid(inputs=[InputDefinition(name='foo_bar', sources=[], depends_on=step_one_no_external_source)])
def step_two(foo_bar):
    foo_bar['foo'] = foo_bar['foo'] + foo_bar['foo']
    return foo_bar


def test_pipeline_meta():
    pipeline = dagster.pipeline(solids=[step_one_no_external_source, step_two])
    assert list(pipeline.external_inputs) == []
