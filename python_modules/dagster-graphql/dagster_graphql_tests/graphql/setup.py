from graphql import graphql

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.schema import create_schema

from dagster import (
    Any,
    Bool,
    DependencyDefinition,
    Dict,
    Enum,
    EnumValue,
    ExpectationDefinition,
    ExpectationResult,
    Field,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    Nullable,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    RepositoryTargetInfo,
    SolidDefinition,
    String,
    lambda_solid,
    resource,
    solid,
)
from dagster.utils import script_relative_path
from dagster_pandas import DataFrame


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        # executor=GeventObservableExecutor(),
        allow_subscriptions=True,
        return_promise=False,
    )

    # has to check attr because in subscription case it returns AnonymousObservable
    if hasattr(result, 'errors') and result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, 'original_error') and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result


# TODO: super lame to pass throught repo_config
# See https://github.com/dagster-io/dagster/issues/1345
def define_context(repo_config=None, raise_on_error=True):
    return DagsterGraphQLContext(
        repository_target_info=RepositoryTargetInfo.for_pipeline_fn(
            define_repository, kwargs={'repo_config': repo_config}
        ),
        pipeline_runs=PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
        raise_on_error=raise_on_error,
    )


@lambda_solid(inputs=[InputDefinition('num', DataFrame)], output=OutputDefinition(DataFrame))
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(inputs=[InputDefinition('sum_df', DataFrame)], output=OutputDefinition(DataFrame))
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum'] ** 2
    return sum_sq_df


@lambda_solid(
    inputs=[
        InputDefinition(
            'sum_df',
            DataFrame,
            expectations=[
                ExpectationDefinition(
                    name='some_expectation',
                    expectation_fn=lambda _i, _v: ExpectationResult(success=True),
                )
            ],
        )
    ],
    output=OutputDefinition(
        DataFrame,
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


def pandas_hello_world_solids_config():
    return {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}}}
        }
    }


def pandas_hello_world_solids_config_fs_storage():
    return {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}}}
        },
        'storage': {'filesystem': {}},
    }


def define_repository(repo_config=None):
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'more_complicated_config': define_more_complicated_config,
            'more_complicated_nested_config': define_more_complicated_nested_config,
            'pandas_hello_world': get_define_pandas_hello_world('pandas_hello_world'),
            'pandas_hello_world_with_presets': get_define_pandas_hello_world(
                'pandas_hello_world_with_presets'
            ),
            'pandas_hello_world_two': define_pipeline_two,
            'pandas_hello_world_with_expectations': define_pandas_hello_world_with_expectations,
            'pipeline_with_list': define_pipeline_with_list,
            'pandas_hello_world_df_input': define_pipeline_with_pandas_df_input,
            'no_config_pipeline': define_no_config_pipeline,
            'scalar_output_pipeline': define_scalar_output_pipeline,
            'pipeline_with_enum_config': define_pipeline_with_enum_config,
            'naughty_programmer_pipeline': define_naughty_programmer_pipeline,
            'secret_pipeline': define_pipeline_with_secret,
            'pipeline_with_step_metadata': define_pipeline_with_step_metadata,
            'pipeline_with_expectations': define_pipeline_with_expectation,
            'multi_mode_with_resources': define_multi_mode_with_resources_pipeline,
        },
        repo_config=repo_config,
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
                transform_fn=lambda *_args: None,
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
                transform_fn=lambda *_args: None,
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
                                            List(Nullable(Int)), is_optional=True
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


def get_define_pandas_hello_world(name):
    return lambda: PipelineDefinition(
        name=name,
        solids=[sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
    )


def define_pandas_hello_world_with_expectations():
    return PipelineDefinition(
        name='pandas_hello_world_with_expectations',
        solids=[sum_solid, sum_sq_solid, df_expectations_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
            'df_expectations_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
    )


def define_pipeline_two():
    return PipelineDefinition(
        name='pandas_hello_world_two', solids=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_pipeline_with_list():
    return PipelineDefinition(
        name='pipeline_with_list',
        solids=[
            SolidDefinition(
                name='solid_with_list',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_field=Field(List(Int)),
            )
        ],
    )


def define_pipeline_with_pandas_df_input():
    return PipelineDefinition(
        name='pandas_hello_world_df_input',
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
        transform_fn=lambda *args, **kwargs: None,
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
