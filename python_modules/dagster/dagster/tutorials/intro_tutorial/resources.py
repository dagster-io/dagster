from bigco import PublicCloudConn, set_value_in_cloud_store

from dagster import (
    Dict,
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


class PublicCloudStore:
    def __init__(self, username, password):
        # create credential and store it
        self.conn = PublicCloudConn(username, password)

    def record_value(self, context, key, value):
        context.info(
            'Setting key={key} value={value} in cloud'.format(
                key=key, value=value
            )
        )
        set_value_in_cloud_store(self.conn, key, value)


class InMemoryStore:
    def __init__(self):
        self.values = {}

    def record_value(self, context, key, value):
        context.info(
            'Setting key={key} value={value} in memory'.format(
                key=key, value=value
            )
        )
        self.values[key] = value


def define_in_memory_store_resource():
    return ResourceDefinition(
        resource_fn=lambda _: InMemoryStore(),
        description='''
    An in-memory key value store that requires no configuration. Useful for unittesting.
    ''',
    )


def define_cloud_store_resource():
    return ResourceDefinition(
        resource_fn=lambda info: PublicCloudStore(
            info.config['username'], info.config['password']
        ),
        config_field=Field(
            Dict({'username': Field(String), 'password': Field(String)})
        ),
        description='''This represents some cloud-hosted key value store.
        Username and password must be provided via configuration for this to
        work''',
    )


@solid(
    inputs=[InputDefinition('num_one', Int), InputDefinition('num_two', Int)],
    outputs=[OutputDefinition(Int)],
)
def add_ints(info, num_one, num_two):
    result = num_one + num_two
    info.context.resources.store.record_value(info.context, 'add', result)
    return result


def define_resource_test_pipeline():
    return PipelineDefinition(
        name='resource_test_pipeline',
        solids=[add_ints],
        context_definitions={
            'local': PipelineContextDefinition(
                resources={'store': define_in_memory_store_resource()}
            ),
            'cloud': PipelineContextDefinition(
                resources={'store': define_cloud_store_resource()}
            ),
        },
    )
