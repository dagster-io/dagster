# from bigco import PublicCloudConn, set_value_in_cloud_store

from dagster import (
    Dict,
    execute_pipeline,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    String,
    solid,
)


class PublicCloudConn:
    def __init__(self, username, password):
        self.username = username
        self.password = password


def set_value_in_cloud_store(_conn, _key, _value):
    # imagine this doing something
    pass


class PublicCloudStore:
    def __init__(self, username, password):
        # create credential and store it
        self.conn = PublicCloudConn(username, password)

    def record_value(self, log, key, value):
        log.info('Setting key={key} value={value} in cloud'.format(key=key, value=value))
        set_value_in_cloud_store(self.conn, key, value)


class InMemoryStore:
    def __init__(self):
        self.values = {}

    def record_value(self, log, key, value):
        log.info('Setting key={key} value={value} in memory'.format(key=key, value=value))
        self.values[key] = value


def define_in_memory_store_resource():
    return ResourceDefinition(
        resource_fn=lambda _: InMemoryStore(),
        description='''An in-memory key value store that requires 
        no configuration. Useful for unit testing.''',
    )


def define_cloud_store_resource():
    return ResourceDefinition(
        resource_fn=lambda init_context: PublicCloudStore(
            init_context.resource_config['username'], init_context.resource_config['password']
        ),
        config_field=Field(Dict({'username': Field(String), 'password': Field(String)})),
        description='''This represents some cloud-hosted key value store.
        Username and password must be provided via configuration for this to
        work''',
    )


@solid(
    inputs=[InputDefinition('num_one', Int), InputDefinition('num_two', Int)],
    outputs=[OutputDefinition(Int)],
)
def add_ints(context, num_one, num_two):
    sum_ints = num_one + num_two
    context.resources.store.record_value(context.log, 'add', sum_ints)
    return sum_ints


def define_resource_test_pipeline():
    return PipelineDefinition(
        name='resource_test_pipeline',
        solids=[add_ints],
        context_definitions={
            'local': PipelineContextDefinition(
                resources={'store': define_in_memory_store_resource()}
            ),
            'cloud': PipelineContextDefinition(resources={'store': define_cloud_store_resource()}),
        },
    )


if __name__ == '__main__':
    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment_dict={
            'context': {
                'cloud': {
                    'resources': {
                        'store': {'config': {'username': 'some_user', 'password': 'some_password'}}
                    }
                }
            },
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 6}}}},
        },
    )

    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment_dict={
            'context': {'local': {}},
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 6}}}},
        },
    )
