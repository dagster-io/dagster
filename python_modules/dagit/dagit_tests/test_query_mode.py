import json
import subprocess

from dagster.utils import script_relative_path


def test_basic_introspection():
    query = '{ __schema { types { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-y', repo_path])

    result_data = json.loads(result)
    assert result_data['data']


def test_basic_pipelines():
    query = '{ pipelines { nodes { name } } }'

    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-y', repo_path])

    result_data = json.loads(result)
    assert result_data['data']


def test_basic_variables():
    query = 'query FooBar($pipelineName: String!){ pipeline(params:{name: $pipelineName}){ name} }'
    variables = '{"pipelineName": "pandas_hello_world"}'
    repo_path = script_relative_path('./repository.yml')

    result = subprocess.check_output(['dagit', '-q', query, '-v', variables, '-y', repo_path])
    result_data = json.loads(result)
    assert result_data['data']
