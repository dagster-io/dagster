# pylint: disable=W0622,W0614,W0401
from dagster import *


class PublicCloudConn:
    pass


def create_public_cloud_conn(_creds):
    return PublicCloudConn()


def set_value_in_cloud_store(_conn, _key, _value):
    # imagine this doing something
    pass


class PublicCloudStoreResource:
    def __init__(self, credentials):
        # create credential and store it
        self.conn = create_public_cloud_conn(credentials)

    def record_value(self, key, value):
        set_value_in_cloud_store(self.conn, key, value)


@solid(config_def=ConfigDefinition(types.Int), outputs=[OutputDefinition(types.Int)])
def injest_a(_context, conf):
    return conf


@solid(
    config_def=ConfigDefinition(types.Int),
    outputs=[OutputDefinition(types.Int)],
)
def injest_b(_context, conf):
    return conf


@solid(
    inputs=[InputDefinition('num_one', types.Int),
            InputDefinition('num_two', types.Int)],
    outputs=[OutputDefinition(types.Int)],
)
def add_ints(_context, _conf, num_one, num_two):
    return num_one + num_two


@solid(
    inputs=[InputDefinition('num_one', types.Int),
            InputDefinition('num_two', types.Int)],
    outputs=[OutputDefinition(types.Int)],
)
def mult_ints(_context, _conf, num_one, num_two):
    return num_one * num_two


def define_part_nine_step_one():
    return PipelineDefinition(
        name='part_nine_step_one',
        solids=[injest_a, injest_b, add_ints, mult_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
            'mult_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
        },
    )


def test_intro_tutorial_part_nine_step_one():
    result = execute_pipeline(
        define_part_nine_step_one(),
        config.Environment(solids={
            'injest_a': config.Solid(2),
            'injest_b': config.Solid(3),
        })
    )

    assert result.success
    assert result.result_for_solid('injest_a').transformed_value() == 2
    assert result.result_for_solid('injest_b').transformed_value() == 3
    assert result.result_for_solid('add_ints').transformed_value() == 5
    assert result.result_for_solid('mult_ints').transformed_value() == 6
