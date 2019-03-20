import subprocess

from dagster.seven import json
from dagster.utils import script_relative_path


def test_basic_introspection():
    query = '{ __schema { types { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit-cli', '-q', query, '-y', repo_path])

    result_data = json.loads(result.decode())
    assert result_data['data']


def test_no_watch_mode():
    query = '{ __schema { types { name } } }'

    repo_path = script_relative_path('./repository.yml')

    # Runs the dagit wrapper instead of dagit-cli to ensure it still runs sync with --no-watch
    result = subprocess.check_output(['dagit', '--no-watch', '-q', query, '-y', repo_path])

    result_data = json.loads(result.decode())
    assert result_data['data']


def test_basic_pipelines():
    query = '{ pipelines { nodes { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit-cli', '-q', query, '-y', repo_path])

    result_data = json.loads(result.decode())
    assert result_data['data']


def test_basic_variables():
    query = 'query FooBar($pipelineName: String!){ pipeline(params:{name: $pipelineName}){ name} }'
    variables = '{"pipelineName": "pandas_hello_world"}'
    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit-cli', '-q', query, '-v', variables, '-y', repo_path])
    result_data = json.loads(result.decode())
    assert result_data['data']


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


def test_start_execution():
    path = script_relative_path('./num.csv')

    variables = json.dumps(
        {
            "pipeline": {"name": "pandas_hello_world"},
            "config": {"solids": {"sum_solid": {"inputs": {"num": {"csv": {"path": path}}}}}},
        }
    )

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(
        ['dagit-cli', '-q', START_PIPELINE_EXECUTION_QUERY, '-v', variables, '-y', repo_path]
    )
    decoded = result.decode()
    try:
        result_data = json.loads(result.decode())
        assert result_data['data']
    except Exception as e:
        raise Exception('Failed with {} Exception: {}'.format(decoded, e))
