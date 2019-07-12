# pylint: disable=no-value-for-parameter

import csv
import logging
from collections import OrderedDict
from copy import deepcopy

from dagster import (
    composite_solid,
    Any,
    Bool,
    Dict,
    Enum,
    EnumValue,
    EventMetadataEntry,
    ExecutionTargetHandle,
    ExpectationResult,
    Field,
    InputDefinition,
    Int,
    List,
    Materialization,
    ModeDefinition,
    Optional,
    Output,
    OutputDefinition,
    Path,
    PresetDefinition,
    RepositoryDefinition,
    SolidDefinition,
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


@solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_defs=[OutputDefinition(PoorMansDataFrame)],
)
def df_expectations_solid(_context, sum_df):
    yield ExpectationResult(label="some_expectation", success=True)
    yield ExpectationResult(label="other_expecation", success=True)
    yield Output(sum_df)


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
        pipeline_defs=[
            composites_pipeline,
            csv_hello_world,
            csv_hello_world_df_input,
            csv_hello_world_two,
            csv_hello_world_with_expectations,
            materialization_pipeline,
            more_complicated_config,
            more_complicated_nested_config,
            multi_mode_with_loggers,
            multi_mode_with_resources,
            naughty_programmer_pipeline,
            no_config_pipeline,
            pipeline_with_enum_config,
            pipeline_with_expectations,
            pipeline_with_list,
            pipeline_with_step_metadata,
            scalar_output_pipeline,
            secret_pipeline,
        ],
    )


@pipeline
def pipeline_with_expectations():
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

    emit_successful_expectation()
    emit_failed_expectation()
    emit_successful_expectation_no_metadata()


@pipeline
def secret_pipeline():
    @solid(
        config_field=Field(
            Dict({'password': Field(String, is_secret=True), 'notpassword': Field(String)})
        )
    )
    def solid_with_secret(_context):
        pass

    return solid_with_secret()


@pipeline
def more_complicated_config():
    @solid(
        config={
            'field_one': Field(String),
            'field_two': Field(String, is_optional=True),
            'field_three': Field(String, is_optional=True, default_value='some_value'),
        }
    )
    def a_solid_with_three_field_config(_context):
        return None

    return a_solid_with_three_field_config()


@pipeline
def more_complicated_nested_config():
    @solid(
        name='a_solid_with_multilayered_config',
        input_defs=[],
        output_defs=[],
        config_field=Field(
            Dict(
                {
                    'field_one': Field(String),
                    'field_two': Field(String, is_optional=True),
                    'field_three': Field(String, is_optional=True, default_value='some_value'),
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
    def a_solid_with_multilayered_config(_):
        return None

    return a_solid_with_multilayered_config()


@pipeline(
    preset_defs=[
        PresetDefinition(
            name='prod',
            environment_files=[script_relative_path('../environments/csv_hello_world_prod.yaml')],
        ),
        PresetDefinition(
            name='test',
            environment_files=[script_relative_path('../environments/csv_hello_world_test.yaml')],
        ),
    ]
)
def csv_hello_world():
    return sum_sq_solid(sum_df=sum_solid())


@pipeline
def csv_hello_world_with_expectations():
    ss = sum_solid()
    sum_sq_solid(sum_df=ss)
    df_expectations_solid(sum_df=ss)


@pipeline
def csv_hello_world_two():
    return sum_solid()


@pipeline
def pipeline_with_list():
    solid_def = SolidDefinition(
        name='solid_with_list',
        input_defs=[],
        output_defs=[],
        compute_fn=lambda *_args: None,
        config_field=Field(List[Int]),
    )
    solid_def()


@pipeline
def csv_hello_world_df_input():
    return sum_sq_solid(sum_solid())


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return 'Hello'

    return return_hello()


@pipeline
def scalar_output_pipeline():
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

    return_str()
    return_int()
    return_bool()
    return_any()


@pipeline
def pipeline_with_enum_config():
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

    return takes_an_enum()


@pipeline
def naughty_programmer_pipeline():
    @lambda_solid
    def throw_a_thing():
        raise Exception('bad programmer, bad')

    return throw_a_thing()


@pipeline
def pipeline_with_step_metadata():
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
    return solid_def()


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


@pipeline(
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
    preset_defs=[PresetDefinition("add", mode="add_mode")],
)
def multi_mode_with_resources():
    @solid
    def apply_to_three(context):
        return context.resources.op(3)

    return apply_to_three()


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


@pipeline(
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
    ]
)
def multi_mode_with_loggers():
    @solid
    def return_six(context):
        context.log.critical('OMG!')
        return 6

    return return_six()


@pipeline
def composites_pipeline():
    @lambda_solid(input_defs=[InputDefinition('num', Int)])
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num')])
    def div_two(num):
        return num / 2

    @composite_solid
    def add_two(num):
        return add_one.alias('adder_2')(add_one.alias('adder_1')(num))

    @composite_solid
    def add_four(num):
        return add_two.alias('adder_2')(add_two.alias('adder_1')(num))

    @composite_solid
    def div_four(num):
        return div_two.alias('div_2')(div_two.alias('div_1')(num))

    return div_four(add_four())


@pipeline
def materialization_pipeline():
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

    materialize()  # pylint: disable=no-value-for-parameter
