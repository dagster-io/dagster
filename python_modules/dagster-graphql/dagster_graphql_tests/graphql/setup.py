import csv
import logging
from collections import OrderedDict
from copy import deepcopy


from dagster import (
    Any,
    Bool,
    CompositeSolidDefinition,
    DependencyDefinition,
    Dict,
    Enum,
    EnumValue,
    ExecutionTargetHandle,
    ExpectationDefinition,
    ExpectationResult,
    Field,
    Float,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    Optional,
    OutputDefinition,
    Path,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    SolidDefinition,
    SolidInstance,
    String,
    as_dagster_type,
    input_schema,
    lambda_solid,
    logger,
    output_schema,
    resource,
    solid,
)
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils import script_relative_path
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage


class PoorMansDataFrame_(list):
    pass


@input_schema(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return PoorMansDataFrame_(
            [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]
        )


@output_schema(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return path


PoorMansDataFrame = as_dagster_type(
    PoorMansDataFrame_, input_schema=df_input_schema, output_schema=df_output_schema
)


def define_context(raise_on_error=True):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(define_repository),
        pipeline_runs=PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
        raise_on_error=raise_on_error,
    )


@lambda_solid(
    inputs=[InputDefinition('num', PoorMansDataFrame)], output=OutputDefinition(PoorMansDataFrame)
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = int(x['num1']) + int(x['num2'])
    return PoorMansDataFrame(sum_df)


@lambda_solid(
    inputs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output=OutputDefinition(PoorMansDataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = deepcopy(sum_df)
    for x in sum_sq_df:
        x['sum_sq'] = int(x['sum']) ** 2
    return PoorMansDataFrame(sum_sq_df)


@lambda_solid(
    inputs=[
        InputDefinition(
            'sum_df',
            PoorMansDataFrame,
            expectations=[
                ExpectationDefinition(
                    name='some_expectation',
                    expectation_fn=lambda _i, _v: ExpectationResult(success=True),
                )
            ],
        )
    ],
    output=OutputDefinition(
        PoorMansDataFrame,
        expectations=[
            ExpectationDefinition(
                name='other_expectation',
                expectation_fn=lambda _i, _v: ExpectationResult(success=True),
            )
        ],
    ),
)
def df_expectations_solid(sum_df):
    return sum_df


def csv_hello_world_solids_config():
    return {'solids': {'sum_solid': {'inputs': {'num': script_relative_path('../data/num.csv')}}}}


def csv_hello_world_solids_config_fs_storage():
    return {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('../data/num.csv')}}},
        'storage': {'filesystem': {}},
    }


def define_repository():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'more_complicated_config': define_more_complicated_config,
            'more_complicated_nested_config': define_more_complicated_nested_config,
            'csv_hello_world': define_csv_hello_world,
            'csv_hello_world_two': define_pipeline_two,
            'csv_hello_world_with_expectations': define_csv_hello_world_with_expectations,
            'pipeline_with_list': define_pipeline_with_list,
            'csv_hello_world_df_input': define_pipeline_with_csv_df_input,
            'no_config_pipeline': define_no_config_pipeline,
            'scalar_output_pipeline': define_scalar_output_pipeline,
            'pipeline_with_enum_config': define_pipeline_with_enum_config,
            'naughty_programmer_pipeline': define_naughty_programmer_pipeline,
            'secret_pipeline': define_pipeline_with_secret,
            'pipeline_with_step_metadata': define_pipeline_with_step_metadata,
            'pipeline_with_expectations': define_pipeline_with_expectation,
            'multi_mode_with_resources': define_multi_mode_with_resources_pipeline,
            'multi_mode_with_loggers': define_multi_mode_with_loggers_pipeline,
            'composites_pipeline': define_composites_pipeline,
        },
    )


def define_pipeline_with_expectation():
    @solid(outputs=[])
    def emit_successful_expectation(_context):
        yield ExpectationResult(
            success=True,
            name='always_true',
            message='Successful',
            result_metadata={'reason': 'Just because.'},
        )

    @solid(outputs=[])
    def emit_failed_expectation(_context):
        yield ExpectationResult(
            success=False,
            name='always_false',
            message='Failure',
            result_metadata={'reason': 'Relentless pessimism.'},
        )

    @solid(outputs=[])
    def emit_successful_expectation_no_metadata(_context):
        yield ExpectationResult(success=True, name='no_metadata', message='Successful')

    return PipelineDefinition(
        name='pipeline_with_expectations',
        solids=[
            emit_successful_expectation,
            emit_failed_expectation,
            emit_successful_expectation_no_metadata,
        ],
    )


def define_pipeline_with_secret():
    @solid(
        config_field=Field(
            Dict({'password': Field(String, is_secret=True), 'notpassword': Field(String)})
        )
    )
    def solid_with_secret(_context):
        pass

    return PipelineDefinition(name='secret_pipeline', solids=[solid_with_secret])


def define_more_complicated_config():
    return PipelineDefinition(
        name='more_complicated_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_three_field_config',
                inputs=[],
                outputs=[],
                compute_fn=lambda *_args: None,
                config_field=Field(
                    Dict(
                        {
                            'field_one': Field(String),
                            'field_two': Field(String, is_optional=True),
                            'field_three': Field(
                                String, is_optional=True, default_value='some_value'
                            ),
                        }
                    )
                ),
            )
        ],
    )


def define_more_complicated_nested_config():
    return PipelineDefinition(
        name='more_complicated_nested_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_multilayered_config',
                inputs=[],
                outputs=[],
                compute_fn=lambda *_args: None,
                config_field=Field(
                    Dict(
                        {
                            'field_one': Field(String),
                            'field_two': Field(String, is_optional=True),
                            'field_three': Field(
                                String, is_optional=True, default_value='some_value'
                            ),
                            'nested_field': Field(
                                Dict(
                                    {
                                        'field_four_str': Field(String),
                                        'field_five_int': Field(Int),
                                        'field_six_nullable_int_list': Field(
                                            List[Optional[Int]], is_optional=True
                                        ),
                                    }
                                )
                            ),
                        }
                    )
                ),
            )
        ],
    )


def define_csv_hello_world():
    return PipelineDefinition(
        name='csv_hello_world',
        solids=[sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
        preset_definitions=[
            PresetDefinition(
                name='prod',
                environment_files=[
                    script_relative_path('../environments/csv_hello_world_prod.yaml')
                ],
            ),
            PresetDefinition(
                name='test',
                environment_files=[
                    script_relative_path('../environments/csv_hello_world_test.yaml')
                ],
            ),
        ],
    )


def define_csv_hello_world_with_expectations():
    return PipelineDefinition(
        name='csv_hello_world_with_expectations',
        solids=[sum_solid, sum_sq_solid, df_expectations_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
            'df_expectations_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
    )


def define_pipeline_two():
    return PipelineDefinition(
        name='csv_hello_world_two', solids=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_pipeline_with_list():
    return PipelineDefinition(
        name='pipeline_with_list',
        solids=[
            SolidDefinition(
                name='solid_with_list',
                inputs=[],
                outputs=[],
                compute_fn=lambda *_args: None,
                config_field=Field(List[Int]),
            )
        ],
    )


def define_pipeline_with_csv_df_input():
    return PipelineDefinition(
        name='csv_hello_world_df_input',
        solids=[sum_solid, sum_sq_solid],
        dependencies={'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)}},
    )


def define_no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return PipelineDefinition(name='no_config_pipeline', solids=[return_hello])


def define_scalar_output_pipeline():
    @lambda_solid(output=OutputDefinition(String))
    def return_str():
        return 'foo'

    @lambda_solid(output=OutputDefinition(Int))
    def return_int():
        return 34234

    @lambda_solid(output=OutputDefinition(Bool))
    def return_bool():
        return True

    @lambda_solid(output=OutputDefinition(Any))
    def return_any():
        return 'dkjfkdjfe'

    return PipelineDefinition(
        name='scalar_output_pipeline', solids=[return_str, return_int, return_bool, return_any]
    )


def define_pipeline_with_enum_config():
    @solid(
        config_field=Field(
            Enum(
                'TestEnum',
                [
                    EnumValue(config_value='ENUM_VALUE_ONE', description='An enum value.'),
                    EnumValue(config_value='ENUM_VALUE_TWO', description='An enum value.'),
                    EnumValue(config_value='ENUM_VALUE_THREE', description='An enum value.'),
                ],
            )
        )
    )
    def takes_an_enum(_context):
        pass

    return PipelineDefinition(name='pipeline_with_enum_config', solids=[takes_an_enum])


def define_naughty_programmer_pipeline():
    @lambda_solid
    def throw_a_thing():
        raise Exception('bad programmer, bad')

    return PipelineDefinition(name='naughty_programmer_pipeline', solids=[throw_a_thing])


def define_pipeline_with_step_metadata():
    solid_def = SolidDefinition(
        name='solid_metadata_creation',
        inputs=[],
        outputs=[],
        compute_fn=lambda *args, **kwargs: None,
        config_field=Field(Dict({'str_value': Field(String)})),
        step_metadata_fn=lambda env_config: {
            'computed': env_config.solids['solid_metadata_creation'].config['str_value'] + '1'
        },
    )
    return PipelineDefinition(name='pipeline_with_step_metadata', solids=[solid_def])


def define_multi_mode_with_resources_pipeline():
    @resource(config_field=Field(Int))
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_field=Field(Int))
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config_field=Field(Dict({'num_one': Field(Int), 'num_two': Field(Int)})))
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config['num_one']
            + init_context.resource_config['num_two']
        )

    @solid
    def apply_to_three(context):
        return context.resources.op(3)

    return PipelineDefinition(
        name='multi_mode_with_resources',
        solids=[apply_to_three],
        preset_definitions=[PresetDefinition("add", mode="add_mode")],
        mode_definitions=[
            ModeDefinition(
                name='add_mode',
                resources={'op': adder_resource},
                description='Mode that adds things',
            ),
            ModeDefinition(
                name='mult_mode',
                resources={'op': multer_resource},
                description='Mode that multiplies things',
            ),
            ModeDefinition(
                name='double_adder',
                resources={'op': double_adder_resource},
                description='Mode that adds two numbers to thing',
            ),
        ],
    )


def define_multi_mode_with_loggers_pipeline():
    @logger(config_field=Field(String))
    def foo_logger(init_context):
        logger_ = logging.Logger('foo')
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
        return logger_

    @logger(config_field=Field(Dict({'log_level': Field(String), 'prefix': Field(String)})))
    def bar_logger(init_context):
        class BarLogger(logging.Logger):
            def __init__(self, name, prefix, *args, **kwargs):
                self.prefix = prefix
                super(BarLogger, self).__init__(name, *args, **kwargs)

            def log(self, lvl, msg, *args, **kwargs):  # pylint: disable=arguments-differ
                msg = self.prefix + msg
                super(BarLogger, self).log(lvl, msg, *args, **kwargs)

        logger_ = BarLogger('bar', init_context.logger_config['prefix'])
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config['log_level']))

    @solid
    def return_six(context):
        context.log.critical('OMG!')
        return 6

    return PipelineDefinition(
        name='multi_mode_with_loggers',
        solids=[return_six],
        mode_definitions=[
            ModeDefinition(
                name='foo_mode', loggers={'foo': foo_logger}, description='Mode with foo logger'
            ),
            ModeDefinition(
                name='bar_mode', loggers={'bar': bar_logger}, description='Mode with bar logger'
            ),
            ModeDefinition(
                name='foobar_mode',
                loggers={'foo': foo_logger, 'bar': bar_logger},
                description='Mode with multiple loggers',
            ),
        ],
    )


def define_composites_pipeline():
    @lambda_solid(inputs=[InputDefinition('num', Int)])
    def add_one(num):
        return num + 1

    @lambda_solid(inputs=[InputDefinition('num')])
    def div_two(num):
        return num / 2

    add_two = CompositeSolidDefinition(
        'add_two',
        solids=[add_one],
        dependencies={
            SolidInstance('add_one', 'adder_1'): {},
            SolidInstance('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
        output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
    )

    add_four = CompositeSolidDefinition(
        'add_four',
        solids=[add_two],
        dependencies={
            SolidInstance('add_two', 'adder_1'): {},
            SolidInstance('add_two', 'adder_2'): {'num': DependencyDefinition('adder_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
        output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
    )

    div_four = CompositeSolidDefinition(
        'div_four',
        solids=[div_two],
        dependencies={
            SolidInstance('div_two', 'div_1'): {},
            SolidInstance('div_two', 'div_2'): {'num': DependencyDefinition('div_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('div_1', 'num')],
        output_mappings=[OutputDefinition(Float).mapping_from('div_2')],
    )

    return PipelineDefinition(
        name='composites_pipeline',
        solids=[add_four, div_four],
        dependencies={'div_four': {'num': DependencyDefinition('add_four')}},
    )
