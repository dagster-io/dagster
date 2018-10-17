from dagster import (
    DependencyDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    lambda_solid,
)
import dagster.pandas as dagster_pd

from dagit.schema import create_schema
from dagit.app import RepositoryContainer

from graphql import graphql


@lambda_solid(
    inputs=[InputDefinition('num', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum']**2
    return sum_sq_df


def define_pipeline_one():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[dagster_pd.load_csv_solid('load_num_csv'), sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'sum_sq_solid': {
                'sum_df': DependencyDefinition(sum_solid.name),
            },
        },
    )


def define_pipeline_two():
    return PipelineDefinition(
        name='pandas_hello_world_two',
        solids=[dagster_pd.load_csv_solid('load_num_csv'), sum_solid],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
        },
    )


def define_repo():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'pandas_hello_world': define_pipeline_one,
            'pandas_hello_world_two': define_pipeline_two,
        }
    )


def execute_dagster_graphql(repo, query):
    return graphql(
        create_schema(),
        query,
        context={'repository_container': RepositoryContainer(repository=repo)},
    )


def test_pipelines():
    result = execute_dagster_graphql(define_repo(), '{ pipelines { name } }')
    assert result.data
    assert not result.errors

    assert set([p['name'] for p in result.data['pipelines']]) == set(
        ['pandas_hello_world', 'pandas_hello_world_two']
    )


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_repo(), '''
    { 
        pipeline(name: "pandas_hello_world_two") { 
            name 
        }
    }'''
    )

    assert result.data
    assert not result.errors
    assert result.data['pipeline']['name'] == 'pandas_hello_world_two'
