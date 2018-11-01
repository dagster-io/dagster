from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    SolidDefinition,
    lambda_solid,
    types,
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
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
            sum_sq_solid,
        ],
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
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
        },
    )


def define_more_complicated_config():
    return PipelineDefinition(
        name='more_complicated_config',
        solids=[
            SolidDefinition(
                name='a_solid_with_config',
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
                config_def=ConfigDefinition(
                    types.ConfigDictionary(
                        'SomeSolidWithConfig',
                        {
                            'field_one':
                            types.Field(types.String),
                            'field_two':
                            types.Field(types.String, is_optional=True),
                            'field_three':
                            types.Field(
                                types.String,
                                is_optional=True,
                                default_value='some_value',
                            )
                        },
                    )
                )
            )
        ]
    )


def define_repo():
    return RepositoryDefinition(
        name='test',
        pipeline_dict={
            'pandas_hello_world': define_pipeline_one,
            'pandas_hello_world_two': define_pipeline_two,
            'more_complicated_config': define_more_complicated_config,
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
        [
            'pandas_hello_world',
            'pandas_hello_world_two',
            'more_complicated_config',
        ]
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


def test_production_query():
    result = execute_dagster_graphql(
        define_repo(),
        PRODUCTION_QUERY,
    )

    if result.errors:
        raise Exception(result.errors)

    assert result.data
    assert not result.errors


PRODUCTION_QUERY = '''
query AppQuery {
  pipelinesOrErrors {
    ... on Error {
      message
      stack
      __typename
    }
    ... on Pipeline {
      ...PipelineFragment
      __typename
    }
    __typename
  }
}

fragment PipelineFragment on Pipeline {
  name
  description
  solids {
    ...SolidFragment
    __typename
  }
  contexts {
    name
    description
    config {
      ...ConfigFragment
      __typename
    }
    __typename
  }
  ...PipelineGraphFragment
  ...ConfigEditorFragment
  __typename
}

fragment SolidFragment on Solid {
  ...SolidTypeSignatureFragment
  name
  definition {
    description
    metadata {
      key
      value
      __typename
    }
    configDefinition {
      ...ConfigFragment
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      description
      type {
        ...TypeWithTooltipFragment
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      description
      type {
        ...TypeWithTooltipFragment
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment TypeWithTooltipFragment on Type {
  name
  description
  typeAttributes {
    isBuiltin
    isSystemConfig
  }
  __typename
}

fragment SolidTypeSignatureFragment on Solid {
  outputs {
    definition {
      name
      type {
        ...TypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  inputs {
    definition {
      name
      type {
        ...TypeWithTooltipFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigFragment on Config {
  type {
    __typename
    name
    description
    ... on CompositeType {
      fields {
        name
        description
        isOptional
        defaultValue
        type {
          name
          description
          ...TypeWithTooltipFragment
          ... on CompositeType {
            fields {
              name
              description
              isOptional
              defaultValue
              type {
                name
                description
                ...TypeWithTooltipFragment
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      ...TypeWithTooltipFragment
      __typename
    }
  }
  __typename
}

fragment PipelineGraphFragment on Pipeline {
  name
  solids {
    ...SolidNodeFragment
    __typename
  }
  __typename
}

fragment SolidNodeFragment on Solid {
  name
  inputs {
    definition {
      name
      type {
        name
        __typename
      }
      __typename
    }
    dependsOn {
      definition {
        name
        __typename
      }
      solid {
        name
        __typename
      }
      __typename
    }
    __typename
  }
  outputs {
    definition {
      name
      type {
        name
        __typename
      }
      expectations {
        name
        description
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ConfigEditorFragment on Pipeline {
  name
  ...ConfigExplorerFragment
  __typename
}

fragment ConfigExplorerFragment on Pipeline {
  contexts {
    name
    description
    config {
      ...ConfigFragment
      __typename
    }
    __typename
  }
  solids {
    definition {
      name
      description
      configDefinition {
        ...ConfigFragment
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}
'''