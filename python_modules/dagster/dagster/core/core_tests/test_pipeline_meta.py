import dagster
from dagster.core.definitions import InputDefinition
from dagster.core.decorators import solid


@solid()
def step_one_no_external_source():
    return {'foo': 'bar'}


@solid(inputs=[InputDefinition(name='foo_bar', depends_on=step_one_no_external_source)])
def step_two(foo_bar):
    foo_bar['foo'] = foo_bar['foo'] + foo_bar['foo']
    return foo_bar
