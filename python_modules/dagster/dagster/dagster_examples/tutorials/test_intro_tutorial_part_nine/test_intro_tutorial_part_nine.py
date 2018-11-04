# pylint: disable=W0622,W0614,W0401
from collections import namedtuple
from logging import DEBUG
import yaml

import pytest

from dagster import (
    ConfigDefinition,
    DagsterTypeError,
    DependencyDefinition,
    ExecutionContext,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)


class PublicCloudConn:
    def __init__(self, creds):
        self.creds = creds


def set_value_in_cloud_store(_conn, _key, _value):
    # imagine this doing something
    pass


class PublicCloudStore:
    def __init__(self, credentials):
        # create credential and store it
        self.conn = PublicCloudConn(credentials)

    def record_value(self, context, key, value):
        context.info('Setting key={key} value={value} in cloud'.format(key=key, value=value))
        set_value_in_cloud_store(self.conn, key, value)


class InMemoryStore:
    def __init__(self):
        self.values = {}

    def record_value(self, context, key, value):
        context.info('Setting key={key} value={value} in memory'.format(key=key, value=value))
        self.values[key] = value


PartNineResources = namedtuple('PartNineResources', 'store')


def define_contextless_solids():
    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(info):
        return info.config

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_b(info):
        return info.config

    @lambda_solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        output=OutputDefinition(types.Int),
    )
    def add_ints(num_one, num_two):
        return num_one + num_two

    @lambda_solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        output=OutputDefinition(types.Int),
    )
    def mult_ints(num_one, num_two):
        return num_one * num_two

    return [injest_a, injest_b, add_ints, mult_ints]


def define_contextful_solids():
    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(info):
        info.context.resources.store.record_value(info.context, 'a', info.config)
        return info.config

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_b(info):
        info.context.resources.store.record_value(info.context, 'b', info.config)
        return info.config

    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(info, num_one, num_two):
        result = num_one + num_two
        info.context.resources.store.record_value(info.context, 'add', result)
        return result

    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def mult_ints(info, num_one, num_two):
        result = num_one * num_two
        info.context.resources.store.record_value(info.context, 'mult', result)
        return result

    return [injest_a, injest_b, add_ints, mult_ints]


def define_part_nine_step_one_pipeline():
    return PipelineDefinition(
        name='part_nine_step_one_pipeline',
        solids=define_contextless_solids(),
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


PartNineResources = namedtuple('PartNineResources', 'store')


def define_part_nine_step_two_pipeline():
    return PipelineDefinition(
        name='part_nine_step_two_pipeline',
        solids=define_contextful_solids(),
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
        context_definitions={
            'local':
            PipelineContextDefinition(
                context_fn=lambda *_args:
                    ExecutionContext.console_logging(
                        log_level=DEBUG,
                        resources=PartNineResources(InMemoryStore())
                    )
            ),
        }
    )


def define_part_nine_final_pipeline():
    return PipelineDefinition(
        name='part_nine_final_pipeline',
        solids=define_contextful_solids(),
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
        context_definitions={
            'local':
            PipelineContextDefinition(
                context_fn=lambda *_args: ExecutionContext.console_logging(
                    log_level=DEBUG,
                    resources=PartNineResources(InMemoryStore())
                )
            ),
            'cloud':
            PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext.console_logging(
                    resources=PartNineResources(PublicCloudStore(info.config['credentials']))
                ),
                config_def=ConfigDefinition(config_type=types.ConfigDictionary(
                    name='CloudConfigDict',
                    fields={
                    'credentials': Field(types.ConfigDictionary(
                        name='CredentialsConfigDict',
                        fields={
                        'user' : Field(types.String),
                        'pass' : Field(types.String),
                    })),
                })),
            )
        }
    )


def define_part_nine_repo():
    return RepositoryDefinition(
        name='part_nine_repo',
        pipeline_dict={
            'part_nine_step_one': define_part_nine_step_one_pipeline,
            'part_nine_final': define_part_nine_final_pipeline,
        }
    )


def test_intro_tutorial_part_nine_step_one():
    result = execute_pipeline(
        define_part_nine_step_one_pipeline(),
        yaml.load(
            '''
solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
context:
    default:
        config:
            log_level: DEBUG
'''
        )
    )

    assert result.success
    assert result.result_for_solid('injest_a').transformed_value() == 2
    assert result.result_for_solid('injest_b').transformed_value() == 3
    assert result.result_for_solid('add_ints').transformed_value() == 5
    assert result.result_for_solid('mult_ints').transformed_value() == 6


def test_intro_tutorial_part_nine_step_one_with_various_defaults():
    yaml_variants = [
        '''
solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
context:
    default:
        config:
''',
        '''
solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
context:
    default:
''',
        '''
solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
context:
''',
        '''
solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
''',
    ]
    for yaml_variant in yaml_variants:

        result = execute_pipeline(
            define_part_nine_step_one_pipeline(),
            yaml.load(yaml_variant),
        )

        assert result.success
        assert result.result_for_solid('injest_a').transformed_value() == 2
        assert result.result_for_solid('injest_b').transformed_value() == 3
        assert result.result_for_solid('add_ints').transformed_value() == 5
        assert result.result_for_solid('mult_ints').transformed_value() == 6


def test_intro_tutorial_part_nine_final_local_success():
    result = execute_pipeline(
        define_part_nine_final_pipeline(),
        yaml.load(
            '''
context:
    local:

solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
'''
        ),
    )

    assert result.success
    assert result.result_for_solid('injest_a').transformed_value() == 2
    assert result.result_for_solid('injest_b').transformed_value() == 3
    assert result.result_for_solid('add_ints').transformed_value() == 5
    assert result.result_for_solid('mult_ints').transformed_value() == 6

    assert result.context.resources.store.values == {
        'a': 2,
        'b': 3,
        'add': 5,
        'mult': 6,
    }


def test_intro_tutorial_part_nine_final_cloud_success():
    result = execute_pipeline(
        define_part_nine_final_pipeline(),
        yaml.load(
            '''
context:
    cloud:
        config:
            credentials:
                user: some_user
                pass: some_password

solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
'''
        ),
    )

    assert result.success


def test_intro_tutorial_part_nine_final_error():
    with pytest.raises(DagsterTypeError, match='Field "username" is not defined'):
        execute_pipeline(
            define_part_nine_final_pipeline(),
            yaml.load(
                '''
context:
    cloud:
        config:
            credentials:
                username: some_user
                pass: some_password

solids:
    injest_a:
        config: 2
    injest_b:
        config: 3
'''
            ),
        )
