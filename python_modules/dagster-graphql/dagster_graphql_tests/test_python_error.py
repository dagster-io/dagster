import sys

from dagster import (
    ExecutionTargetHandle,
    Field,
    Int,
    PipelineDefinition,
    RepositoryDefinition,
    solid,
)

from dagster.utils.error import serializable_error_info_from_exc_info

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage
from dagster_graphql.schema.errors import DauphinPythonError

from dagster_graphql.test.utils import execute_dagster_graphql


def test_python_error():
    def func():
        raise Exception('bar')

    try:
        func()
    except:  # pylint: disable=W0702
        python_error = DauphinPythonError(serializable_error_info_from_exc_info(sys.exc_info()))

    assert python_error
    assert isinstance(python_error.message, str)
    assert isinstance(python_error.stack, list)
    assert len(python_error.stack) == 2
    assert 'bar' in python_error.stack[1]


def define_bad_pipeline():
    @solid(config_field=Field(Int, default_value='number'))
    def bad_context():
        pass

    return PipelineDefinition(name='bad', solid_defs=[bad_context])


def define_error_pipeline_repo():
    return RepositoryDefinition(name='error_pipeline', pipeline_dict={'bad': define_bad_pipeline})


PIPELINES = '''
{
  pipelinesOrError {
    ... on PythonError {
      __typename
      message
    }
  }
}
'''


def test_pipelines_python_error():
    ctx = DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(define_error_pipeline_repo),
        pipeline_runs=PipelineRunStorage(),
        execution_manager=SynchronousExecutionManager(),
    )
    result = execute_dagster_graphql(ctx, PIPELINES)
    assert result.data['pipelinesOrError']['__typename'] == "PythonError"
