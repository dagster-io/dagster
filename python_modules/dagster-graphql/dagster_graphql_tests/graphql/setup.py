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
    EventMetadataEntry,
    ExecutionTargetHandle,
    IOExpectationDefinition,
    ExpectationResult,
    Field,
    Float,
    InputDefinition,
    Int,
    List,
    Materialization,
    ModeDefinition,
    Optional,
    Output,
    OutputDefinition,
    Path,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    SolidDefinition,
    SolidInvocation,
    String,
    as_dagster_type,
    input_hydration_config,
    lambda_solid,
    logger,
    output_materialization_config,
    pipeline,
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


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return PoorMansDataFrame_(
            [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]
        )


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = as_dagster_type(
    PoorMansDataFrame_,
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def define_context(raise_on_error=True, log_dir=None):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(define_repository),
        pipeline_runs=PipelineRunStorage(log_dir),
        execution_manager=SynchronousExecutionManager(),
        raise_on_error=raise_on_error,
    )


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = int(x['num1']) + int(x['num2'])
    return PoorMansDataFrame(sum_df)


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = deepcopy(sum_df)
    for x in sum_sq_df:
        x['sum_sq'] = int(x['sum']) ** 2
    return PoorMansDataFrame(sum_sq_df)


@lambda_solid(
    input_defs=[
        InputDefinition(
            'sum_df',
            PoorMansDataFrame,
            expectations=[
                IOExpectationDefinition(
                    name='some_expectation',
                    expectation_fn=lambda _i, _v: ExpectationResult(success=True),
                )
            ],
        )
    ],
    output_def=OutputDefinition(
        PoorMansDataFrame,
        expectations=[
            IOExpectationDefinition(
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
            'materialization_pipeline': materialization_pipeline,
        },
    )


def define_pipeline_with_expectation():
    @solid(output_defs=[])
    def emit_successful_expectation(_context):
        yield ExpectationResult(
            success=True,
            label='always_true',
            description='Successful',
            metadata_entries=[
                EventMetadataEntry.json(label='data', data={'reason': 'Just because.'})
            ],
        )

    @solid(output_defs=[])
    def emit_failed_expectation(_context):
        yield ExpectationResult(
            success=False,
            label='always_false',
            description='Failure',
            metadata_entries=[
                EventMetadataEntry.json(label='data', data={'reason': 'Relentless pessimism.'})
            ],
        )

    @solid(output_defs=[])
    def emit_successful_expectation_no_metadata(_context):
        yield ExpectationResult(success=True, label='no_metadata', description='Successful')

    return PipelineDefinition(
        name='pipeline_with_expectations',
        solid_defs=[
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

    return PipelineDefinition(name='secret_pipeline', solid_defs=[solid_with_secret])


def define_more_complicated_config():
    return PipelineDefinition(
        name='more_complicated_config',
        solid_defs=[
            SolidDefinition(
                name='a_solid_with_three_field_config',
                input_defs=[],
                output_defs=[],
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
        solid_defs=[
            SolidDefinition(
                name='a_solid_with_multilayered_config',
                input_defs=[],
                output_defs=[],
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
        solid_defs=[sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
        preset_defs=[
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
        solid_defs=[sum_solid, sum_sq_solid, df_expectations_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
            'df_expectations_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
    )


def define_pipeline_two():
    return PipelineDefinition(
        name='csv_hello_world_two', solid_defs=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_pipeline_with_list():
    return PipelineDefinition(
        name='pipeline_with_list',
        solid_defs=[
            SolidDefinition(
                name='solid_with_list',
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
                config_field=Field(List[Int]),
            )
        ],
    )


def define_pipeline_with_csv_df_input():
    return PipelineDefinition(
        name='csv_hello_world_df_input',
        solid_defs=[sum_solid, sum_sq_solid],
        dependencies={'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)}},
    )


def define_no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return PipelineDefinition(name='no_config_pipeline', solid_defs=[return_hello])


def define_scalar_output_pipeline():
    @lambda_solid(output_def=OutputDefinition(String))
    def return_str():
        return 'foo'

    @lambda_solid(output_def=OutputDefinition(Int))
    def return_int():
        return 34234

    @lambda_solid(output_def=OutputDefinition(Bool))
    def return_bool():
        return True

    @lambda_solid(output_def=OutputDefinition(Any))
    def return_any():
        return 'dkjfkdjfe'

    return PipelineDefinition(
        name='scalar_output_pipeline', solid_defs=[return_str, return_int, return_bool, return_any]
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

    return PipelineDefinition(name='pipeline_with_enum_config', solid_defs=[takes_an_enum])


def define_naughty_programmer_pipeline():
    @lambda_solid
    def throw_a_thing():
        raise Exception('bad programmer, bad')

    return PipelineDefinition(name='naughty_programmer_pipeline', solid_defs=[throw_a_thing])


def define_pipeline_with_step_metadata():
    solid_def = SolidDefinition(
        name='solid_metadata_creation',
        input_defs=[],
        output_defs=[],
        compute_fn=lambda *args, **kwargs: None,
        config_field=Field(Dict({'str_value': Field(String)})),
        step_metadata_fn=lambda env_config: {
            'computed': env_config.solids['solid_metadata_creation'].config['str_value'] + '1'
        },
    )
    return PipelineDefinition(name='pipeline_with_step_metadata', solid_defs=[solid_def])


def define_multi_mode_with_resources_pipeline():
    @resource(config_field=Field(Int))
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_field=Field(Int))
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config={'num_one': Field(Int), 'num_two': Field(Int)})
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
        solid_defs=[apply_to_three],
        preset_defs=[PresetDefinition("add", mode="add_mode")],
        mode_defs=[
            ModeDefinition(
                name='add_mode',
                resource_defs={'op': adder_resource},
                description='Mode that adds things',
            ),
            ModeDefinition(
                name='mult_mode',
                resource_defs={'op': multer_resource},
                description='Mode that multiplies things',
            ),
            ModeDefinition(
                name='double_adder',
                resource_defs={'op': double_adder_resource},
                description='Mode that adds two numbers to thing',
            ),
        ],
    )


def define_multi_mode_with_loggers_pipeline():
    @logger(config_field=Field(str))
    def foo_logger(init_context):
        logger_ = logging.Logger('foo')
        logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
        return logger_

    @logger({'log_level': Field(str), 'prefix': Field(str)})
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
        solid_defs=[return_six],
        mode_defs=[
            ModeDefinition(
                name='foo_mode', logger_defs={'foo': foo_logger}, description='Mode with foo logger'
            ),
            ModeDefinition(
                name='bar_mode', logger_defs={'bar': bar_logger}, description='Mode with bar logger'
            ),
            ModeDefinition(
                name='foobar_mode',
                logger_defs={'foo': foo_logger, 'bar': bar_logger},
                description='Mode with multiple loggers',
            ),
        ],
    )


def define_composites_pipeline():
    @lambda_solid(input_defs=[InputDefinition('num', Int)])
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num')])
    def div_two(num):
        return num / 2

    add_two = CompositeSolidDefinition(
        'add_two',
        solid_defs=[add_one],
        dependencies={
            SolidInvocation('add_one', 'adder_1'): {},
            SolidInvocation('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
        output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
    )

    add_four = CompositeSolidDefinition(
        'add_four',
        solid_defs=[add_two],
        dependencies={
            SolidInvocation('add_two', 'adder_1'): {},
            SolidInvocation('add_two', 'adder_2'): {'num': DependencyDefinition('adder_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
        output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
    )

    div_four = CompositeSolidDefinition(
        'div_four',
        solid_defs=[div_two],
        dependencies={
            SolidInvocation('div_two', 'div_1'): {},
            SolidInvocation('div_two', 'div_2'): {'num': DependencyDefinition('div_1')},
        },
        input_mappings=[InputDefinition('num', Int).mapping_to('div_1', 'num')],
        output_mappings=[OutputDefinition(Float).mapping_from('div_2')],
    )

    return PipelineDefinition(
        name='composites_pipeline',
        solid_defs=[add_four, div_four],
        dependencies={'div_four': {'num': DependencyDefinition('add_four')}},
    )


@solid
def materialize(_):
    yield Materialization(
        label='all_types',
        description='a materialization with all metadata types',
        metadata_entries=[
            EventMetadataEntry.text('text is cool', 'text'),
            EventMetadataEntry.url('https://bigty.pe/neato', 'url'),
            EventMetadataEntry.fspath('/tmp/awesome', 'path'),
            EventMetadataEntry.json({'is_dope': True}, 'json'),
        ],
    )
    yield Output(None)


@pipeline
def materialization_pipeline():
    materialize()  # pylint: disable=no-value-for-parameter
