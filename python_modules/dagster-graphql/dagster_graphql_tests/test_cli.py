import json

from click.testing import CliRunner

from dagster import seven
from dagster.utils import script_relative_path

from dagster_graphql.cli import ui


def test_basic_introspection():
    query = '{ __schema { types { name } } }'

    repo_path = script_relative_path('./repository.yml')

    runner = CliRunner()
    result = runner.invoke(ui, ['-y', repo_path, query])

    assert result.exit_code == 0

    result_data = json.loads(result.output)
    assert result_data['data']


def test_basic_pipelines():
    query = '{ pipelines { nodes { name } } }'

    repo_path = script_relative_path('./repository.yml')

    runner = CliRunner()
    result = runner.invoke(ui, ['-y', repo_path, query])

    assert result.exit_code == 0

    result_data = json.loads(result.output)
    assert result_data['data']


def test_basic_variables():
    query = 'query FooBar($pipelineName: String!){ pipeline(params:{name: $pipelineName}){ name} }'
    variables = '{"pipelineName": "math"}'
    repo_path = script_relative_path('./repository.yml')

    runner = CliRunner()
    result = runner.invoke(ui, ['-y', repo_path, '-v', variables, query])

    assert result.exit_code == 0

    result_data = json.loads(result.output)
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
    variables = seven.json.dumps(
        {
            "pipeline": {"name": "math"},
            "config": {"solids": {"add_one": {"inputs": {"num": {"value": 123}}}}},
        }
    )

    repo_path = script_relative_path('./repository.yml')

    runner = CliRunner()
    result = runner.invoke(ui, ['-y', repo_path, '-v', variables, START_PIPELINE_EXECUTION_QUERY])

    assert result.exit_code == 0

    try:
        result_data = json.loads(result.output.strip('\n').split('\n')[-1])
        assert result_data['data']
    except Exception as e:
        raise Exception('Failed with {} Exception: {}'.format(result.output, e))
