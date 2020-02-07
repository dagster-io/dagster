import csv
import logging
import time
from collections import OrderedDict
from copy import deepcopy

from dagster_graphql.test.utils import define_context_for_file, define_subprocess_context_for_file

from dagster import (
    Any,
    Bool,
    Enum,
    EnumValue,
    EventMetadataEntry,
    ExpectationResult,
    Field,
    InputDefinition,
    Int,
    Materialization,
    ModeDefinition,
    Noneable,
    Output,
    OutputDefinition,
    Path,
    PresetDefinition,
    PythonObjectDagsterType,
    RepositoryDefinition,
    String,
    composite_solid,
    input_hydration_config,
    lambda_solid,
    logger,
    output_materialization_config,
    pipeline,
    resource,
    solid,
)
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils import file_relative_path


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name='PoorMansDataFrame',
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def define_test_subprocess_context(instance):
    return define_subprocess_context_for_file(__file__, "define_repository", instance)


def define_test_context(instance=None):
    return define_context_for_file(__file__, "define_repository", instance)


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = int(x['num1']) + int(x['num2'])
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = deepcopy(sum_df)
    for x in sum_sq_df:
        x['sum_sq'] = int(x['sum']) ** 2
    return sum_sq_df


@solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_defs=[OutputDefinition(PoorMansDataFrame)],
)
def df_expectations_solid(_context, sum_df):
    yield ExpectationResult(label="some_expectation", success=True)
    yield ExpectationResult(label="other_expecation", success=True)
    yield Output(sum_df)


def csv_hello_world_solids_config():
    return {
        'solids': {
            'sum_solid': {'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}}
        }
    }


def csv_hello_world_solids_config_fs_storage():
    return {
        'solids': {
            'sum_solid': {'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}}
        },
        'storage': {'filesystem': {}},
    }


@solid(config={'file': Field(Path)})
def loop(context):
    with open(context.solid_config['file'], 'w') as ff:
        ff.write('yup')

    while True:
        time.sleep(0.1)


@pipeline
def infinite_loop_pipeline():
    loop()


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    noop_solid()


def define_repository():
    return RepositoryDefinition(
        name='test',
        pipeline_defs=[
            composites_pipeline,
            csv_hello_world,
            csv_hello_world_df_input,
            csv_hello_world_two,
            csv_hello_world_with_expectations,
            eventually_successful,
            infinite_loop_pipeline,
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
            required_resource_pipeline,
            retry_resource_pipeline,
            scalar_output_pipeline,
            spew_pipeline,
            noop_pipeline,
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
def more_complicated_config():
    @solid(
        config={
            'field_one': Field(String),
            'field_two': Field(String, is_required=False),
            'field_three': Field(String, is_required=False, default_value='some_value'),
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
        config={
            'field_any': Any,
            'field_one': String,
            'field_two': Field(String, is_required=False),
            'field_three': Field(String, is_required=False, default_value='some_value'),
            'nested_field': {
                'field_four_str': String,
                'field_five_int': Int,
                'field_six_nullable_int_list': Field([Noneable(int)], is_required=False),
            },
        },
    )
    def a_solid_with_multilayered_config(_):
        return None

    return a_solid_with_multilayered_config()


@pipeline(
    preset_defs=[
        PresetDefinition.from_files(
            name='prod',
            environment_files=[
                file_relative_path(__file__, '../environments/csv_hello_world_prod.yaml')
            ],
        ),
        PresetDefinition.from_files(
            name='test',
            environment_files=[
                file_relative_path(__file__, '../environments/csv_hello_world_test.yaml')
            ],
        ),
        PresetDefinition(
            name='test_inline',
            environment_dict={
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}
                    }
                }
            },
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


@solid(name='solid_with_list', input_defs=[], output_defs=[], config=[int])
def solid_def(_):
    return None


@pipeline
def pipeline_with_list():
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
        config=Enum(
            'TestEnum',
            [
                EnumValue(config_value='ENUM_VALUE_ONE', description='An enum value.'),
                EnumValue(config_value='ENUM_VALUE_TWO', description='An enum value.'),
                EnumValue(config_value='ENUM_VALUE_THREE', description='An enum value.'),
            ],
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


@resource(config=Field(Int))
def adder_resource(init_context):
    return lambda x: x + init_context.resource_config


@resource(config=Field(Int))
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
    preset_defs=[PresetDefinition.from_files("add", mode="add_mode")],
)
def multi_mode_with_resources():
    @solid(required_resource_keys={'op'})
    def apply_to_three(context):
        return context.resources.op(3)

    return apply_to_three()


@resource(config=Field(Int, is_required=False))
def req_resource(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={'R1': req_resource})])
def required_resource_pipeline():
    @solid(required_resource_keys={'R1'})
    def solid_with_required_resource(_):
        return 1

    solid_with_required_resource()


@logger(config=Field(str))
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
    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num')])
    def div_two(num):
        return num / 2

    @composite_solid(input_defs=[InputDefinition('num', Int)], output_defs=[OutputDefinition(Int)])
    def add_two(num):
        return add_one.alias('adder_2')(add_one.alias('adder_1')(num))

    @composite_solid(input_defs=[InputDefinition('num', Int)], output_defs=[OutputDefinition(Int)])
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

    materialize()


@pipeline
def spew_pipeline():
    @solid
    def spew(_):
        print('HELLO WORLD')

    spew()


def retry_config(count):
    return {
        'resources': {'retry_count': {'config': {'count': count}}},
        'storage': {'filesystem': {}},
    }


@resource(config={'count': Field(Int, is_required=False, default_value=0)})
def retry_config_resource(context):
    return context.resource_config['count']


@pipeline(mode_defs=[ModeDefinition(resource_defs={'retry_count': retry_config_resource})])
def eventually_successful():
    @solid(output_defs=[OutputDefinition(Int)])
    def spawn(_):
        return 0

    @solid(
        input_defs=[InputDefinition('depth', Int)],
        output_defs=[OutputDefinition(Int)],
        required_resource_keys={'retry_count'},
    )
    def fail(context, depth):
        if context.resources.retry_count <= depth:
            raise Exception('fail')

        return depth + 1

    @solid
    def reset(_, depth):
        return depth

    reset(fail(fail(fail(spawn()))))


@resource
def resource_a(_):
    return 'A'


@resource
def resource_b(_):
    return 'B'


@solid(required_resource_keys={'a'})
def start(context):
    assert context.resources.a == 'A'
    return 1


@solid(required_resource_keys={'b'})
def will_fail(context, num):
    assert context.resources.b == 'B'
    raise Exception('fail')


@pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})])
def retry_resource_pipeline():
    will_fail(start())
