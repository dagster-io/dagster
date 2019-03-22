import os
import sys
import uuid

from graphql import parse

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    check,
)

from dagster.core.types.config import ALL_CONFIG_BUILTINS

from dagster.utils import script_relative_path

from dagster_pandas import DataFrame

from dagit.app import RepositoryContainer
from dagit.pipeline_execution_manager import SynchronousExecutionManager
from dagit.pipeline_run_storage import PipelineRunStorage
from dagit.schema.context import DagsterGraphQLContext

from .setup import (
    define_context,
    define_repository,
    execute_dagster_graphql,
    pandas_hello_world_solids_config,
)

# This is needed to find production query in all cases
sys.path.insert(0, os.path.abspath(script_relative_path('.')))

from production_query import (  # pylint: disable=wrong-import-position,wrong-import-order
    PRODUCTION_QUERY,
)


def test_enum_query():
    ENUM_QUERY = '''{
  pipeline(params: { name:"pipeline_with_enum_config" }){
    name
    configTypes {
      __typename
      name
      ... on EnumConfigType {
        values
        {
          value
          description
        }
      }
    }
  }
}
'''

    result = execute_dagster_graphql(define_context(), ENUM_QUERY)

    assert not result.errors
    assert result.data

    enum_type_data = None

    for td in result.data['pipeline']['configTypes']:
        if td['name'] == 'TestEnum':
            enum_type_data = td
            break

    assert enum_type_data
    assert enum_type_data['name'] == 'TestEnum'
    assert enum_type_data['values'] == [
        {'value': 'ENUM_VALUE_ONE', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_TWO', 'description': 'An enum value.'},
        {'value': 'ENUM_VALUE_THREE', 'description': 'An enum value.'},
    ]


TYPE_RENDER_QUERY = '''
fragment innerInfo on ConfigType {
  name
  isList
  isNullable
  innerTypes {
    name
  }
  ... on CompositeConfigType {
    fields {
      name
      configType {
       name
      }
      isOptional
    }
  }  
}

{
  pipeline(params: { name: "more_complicated_nested_config" }) { 
    name
    solids {
      name
      definition {
        configDefinition {
          configType {
            ...innerInfo
            innerTypes {
              ...innerInfo
            }
          }
        }
      }
    }
  }
}
'''


def test_type_rendering():
    result = execute_dagster_graphql(define_context(), TYPE_RENDER_QUERY)
    assert not result.errors
    assert result.data


def define_circular_dependency_pipeline():
    return PipelineDefinition(
        name='circular_dependency_pipeline',
        solids=[
            SolidDefinition(
                name='csolid',
                inputs=[InputDefinition('num', DataFrame)],
                outputs=[OutputDefinition(DataFrame)],
                transform_fn=lambda *_args: None,
            )
        ],
        dependencies={'csolid': {'num': DependencyDefinition('csolid')}},
    )


def test_pipelines():
    result = execute_dagster_graphql(define_context(), '{ pipelines { nodes { name } } }')
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelines']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error():
    result = execute_dagster_graphql(
        define_context(), '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } } '
    )
    assert not result.errors
    assert result.data

    assert {p['name'] for p in result.data['pipelinesOrError']['nodes']} == {
        p.name for p in define_repository().get_all_pipelines()
    }


def test_pipelines_or_error_invalid():
    repository = RepositoryDefinition(
        name='test', pipeline_dict={'pipeline': define_circular_dependency_pipeline}
    )
    context = DagsterGraphQLContext(
        RepositoryContainer(repository=repository),
        PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )
    result = execute_dagster_graphql(
        context, '{ pipelinesOrError { ... on InvalidDefinitionError { message } } }'
    )
    msg = result.data['pipelinesOrError']['message']
    assert "Circular reference detected in solid csolid" in msg


def test_pipeline_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipeline(params: {name: "pandas_hello_world_two"}) {
            name
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipeline']['name'] == 'pandas_hello_world_two'


def test_pipeline_or_error_by_name():
    result = execute_dagster_graphql(
        define_context(),
        '''
    {
        pipelineOrError(params: { name: "pandas_hello_world_two" }) {
          ... on Pipeline {
             name
           }
        }
    }''',
    )

    assert not result.errors
    assert result.data
    assert result.data['pipelineOrError']['name'] == 'pandas_hello_world_two'


def pipeline_named(result, name):
    for pipeline_data in result.data['pipelines']['nodes']:
        if pipeline_data['name'] == name:
            return pipeline_data
    check.failed('Did not find')


def has_config_type_with_key_prefix(pipeline_data, prefix):
    for config_type_data in pipeline_data['configTypes']:
        if config_type_data['key'].startswith(prefix):
            return True

    return False


def has_config_type(pipeline_data, name):
    for config_type_data in pipeline_data['configTypes']:
        if config_type_data['name'] == name:
            return True

    return False


def test_smoke_test_config_type_system():
    result = execute_dagster_graphql(define_context(), ALL_CONFIG_TYPES_QUERY)

    assert not result.errors
    assert result.data

    pipeline_data = pipeline_named(result, 'more_complicated_nested_config')

    assert pipeline_data

    assert has_config_type_with_key_prefix(pipeline_data, 'Dict.')
    assert not has_config_type_with_key_prefix(pipeline_data, 'List.')
    assert not has_config_type_with_key_prefix(pipeline_data, 'Nullable.')

    for builtin_config_type in ALL_CONFIG_BUILTINS:
        assert has_config_type(pipeline_data, builtin_config_type.name)


ALL_CONFIG_TYPES_QUERY = '''
fragment configTypeFragment on ConfigType {
  __typename
  key
  name
  description
  isNullable
  isList
  isSelector
  isBuiltin
  isSystemGenerated
  innerTypes {
    key
    name
    description
    ... on CompositeConfigType {
        fields {
            name
            isOptional
            description
        }
    }
    ... on WrappingConfigType {
        ofType { key }
    }
  }
  ... on EnumConfigType {
    values {
      value
      description
    }
  }
  ... on CompositeConfigType {
    fields {
      name
      isOptional
      description
    }
  }
  ... on WrappingConfigType {
    ofType { key }
  }
}

{
 	pipelines {
    nodes {
      name
      configTypes {
        ...configTypeFragment
      }
    }
  } 
}
'''

CONFIG_TYPE_QUERY = '''
query ConfigTypeQuery($pipelineName: String! $configTypeName: String!)
{
    configTypeOrError(
        pipelineName: $pipelineName
        configTypeName: $configTypeName
    ) {
        __typename
        ... on RegularConfigType {
            name
        }
        ... on CompositeConfigType {
            name
            innerTypes { key name }
            fields { name configType { key name } }
        }
        ... on EnumConfigType {
            name
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on ConfigTypeNotFoundError {
            pipeline { name }
            configTypeName
        }
    }
}
'''


def test_config_type_or_error_query_success():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert result.data['configTypeOrError']['name'] == 'PandasHelloWorld.Environment'


def test_config_type_or_error_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'nope', 'configTypeName': 'PandasHelloWorld.Environment'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'PipelineNotFoundError'
    assert result.data['configTypeOrError']['pipelineName'] == 'nope'


def test_config_type_or_error_type_not_found():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {'pipelineName': 'pandas_hello_world', 'configTypeName': 'nope'},
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'ConfigTypeNotFoundError'
    assert result.data['configTypeOrError']['pipeline']['name'] == 'pandas_hello_world'
    assert result.data['configTypeOrError']['configTypeName'] == 'nope'


def test_config_type_or_error_nested_complicated():
    result = execute_dagster_graphql(
        define_context(),
        CONFIG_TYPE_QUERY,
        {
            'pipelineName': 'more_complicated_nested_config',
            'configTypeName': (
                'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
            ),
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['configTypeOrError']['__typename'] == 'CompositeConfigType'
    assert (
        result.data['configTypeOrError']['name']
        == 'MoreComplicatedNestedConfig.SolidConfig.ASolidWithMultilayeredConfig'
    )
    assert len(result.data['configTypeOrError']['innerTypes']) == 6


def test_production_query():
    result = execute_dagster_graphql(define_context(), PRODUCTION_QUERY)

    assert not result.errors
    assert result.data


ALL_TYPES_QUERY = '''
{
  pipelinesOrError {
    __typename
    ... on PipelineConnection {
      nodes {
        runtimeTypes {
          __typename
          name
        }
        configTypes {
          __typename
          name
          ... on CompositeConfigType {
            fields {
              name
              configType {
                name
                __typename
              }
              __typename
            }
            __typename
          }
        }
        __typename
      }
    }
  }
}
'''


def test_production_config_editor_query():
    result = execute_dagster_graphql(define_context(), ALL_TYPES_QUERY)

    assert not result.errors
    assert result.data


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'pandas_hello_world'


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineConfigValidationInvalid'


def test_basis_start_pipeline_not_found_error():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'sjkdfkdjkf'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'test.csv'}}}}}},
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startPipelineExecution']['pipelineName'] == 'sjkdfkdjkf'


def test_basic_start_pipeline_execution_and_subscribe():
    context = define_context()

    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}}
                    }
                }
            },
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    run_id = result.data['startPipelineExecution']['run']['runId']
    assert uuid.UUID(run_id)

    subscription = execute_dagster_graphql(
        context, parse(SUBSCRIPTION_QUERY), variables={'runId': run_id}
    )

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    assert len(subscribe_results) == 1

    subscribe_result = subscribe_results[0]

    assert not subscribe_result.errors
    assert subscribe_result.data
    assert subscribe_result.data['pipelineRunLogs']
    log_messages = []
    for message in subscribe_result.data['pipelineRunLogs']['messages']:
        if message['__typename'] == 'LogMessageEvent':
            log_messages.append(message)

    # skip the first one was we know it is not associatied with a step
    for log_message in log_messages[1:]:
        assert log_message['step']['key']


def test_subscription_query_error():
    context = define_context(throw_on_user_error=False)

    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={'pipeline': {'name': 'naughty_programmer_pipeline'}},
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    run_id = result.data['startPipelineExecution']['run']['runId']
    assert uuid.UUID(run_id)

    subscription = execute_dagster_graphql(
        context, parse(SUBSCRIPTION_QUERY), variables={'runId': run_id}
    )

    messages = []
    subscription.subscribe(messages.append)

    assert len(messages) == 1
    message = messages[0]
    assert not message.errors
    assert message.data
    assert message.data['pipelineRunLogs']

    step_run_log_entry = _get_step_run_log_entry(
        message.data['pipelineRunLogs'], 'throw_a_thing.transform', 'ExecutionStepFailureEvent'
    )

    assert step_run_log_entry


def _get_step_run_log_entry(pipeline_run_logs, step_key, typename):
    for message_data in pipeline_run_logs['messages']:
        if message_data['__typename'] == typename:
            if message_data['step']['key'] == step_key:
                return message_data


SUBSCRIPTION_QUERY = '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
        messages {
            __typename
            ... on MessageEvent {
                message
                step {key }
            }
        }
    }
}
'''


def test_basic_sync_execution_no_config():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={'pipeline': {'name': 'no_config_pipeline'}, 'config': None},
    )

    assert not result.errors
    assert result.data
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')


def test_basic_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'config': pandas_hello_world_solids_config(),
            'pipeline': {'name': 'pandas_hello_world'},
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'INFO'


def first_event_of_type(logs, message_type):
    for log in logs:
        if log['__typename'] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


START_PIPELINE_EXECUTION_QUERY = '''
mutation ($pipeline: ExecutionSelector!, $config: PipelineConfig) {
    startPipelineExecution(pipeline: $pipeline, config: $config) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { name }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            message
                            level
                        }
                        ... on ExecutionStepStartEvent {
                            step { kind }
                        }
                    }
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''
