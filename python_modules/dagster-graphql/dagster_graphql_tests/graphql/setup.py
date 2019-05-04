from graphql import graphql

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.schema import create_schema

from dagster.cli.dynamic_loader import RepositoryContainer

from dagster.utils import script_relative_path
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
    Nullable,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    ResourceDefinition,
    SolidDefinition,
    String,
    lambda_solid,
    solid,
)
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


def define_context(raise_on_error=True):
    return DagsterGraphQLContext(
        RepositoryContainer(repository=define_repository()),
        PipelineRunStorage(),
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


def define_repository():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'context_config_pipeline': define_context_config_pipeline,
            'more_complicated_config': define_more_complicated_config,
            'more_complicated_nested_config': define_more_complicated_nested_config,
            'pandas_hello_world': define_pandas_hello_world,
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
        },
    )


def define_pipeline_with_expectation():
    @solid(outputs=[])
    def emit_successful_expectation(_context):
        yield ExpectationResult(
            success=True, message='Successful', result_metadata={'reason': 'Just because.'}
        )

    @solid(outputs=[])
    def emit_failed_expectation(_context):
        yield ExpectationResult(
            success=False, message='Failure', result_metadata={'reason': 'Relentless pessimism.'}
        )

    return PipelineDefinition(
        name='pipeline_with_expectations',
        solids=[emit_successful_expectation, emit_failed_expectation],
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


def define_context_config_pipeline():
    return PipelineDefinition(
        name='context_config_pipeline',
        solids=[],
        context_definitions={
            'context_one': PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None, config_field=Field(String)
            ),
            'context_two': PipelineContextDefinition(
                context_fn=lambda *args, **kwargs: None, config_field=Field(Int)
            ),
            'context_with_resources': PipelineContextDefinition(
                resources={
                    'resource_one': ResourceDefinition(
                        resource_fn=lambda *args, **kwargs: None, config_field=Field(Int)
                    ),
                    'resource_two': ResourceDefinition(resource_fn=lambda *args, **kwargs: None),
                }
            ),
        },
    )


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


def define_pandas_hello_world():
    return PipelineDefinition(
        name='pandas_hello_world',
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
