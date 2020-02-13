from dagster_graphql.client.util import (
    execution_params_from_pipeline_run,
    pipeline_run_from_execution_params,
)
from dagster_graphql.schema.roots import execution_params_from_graphql

from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus


def test_roundtrip_run():
    run = PipelineRun(
        pipeline_name='pipey_mcpipeface',
        run_id='8675309',
        environment_dict={'good': True},
        mode='default',
        selector=ExecutionSelector('pipey_mcpipeface'),
        step_keys_to_execute=['step_1', 'step_2', 'step_3'],
        tags={'tag_it': 'bag_it'},
        status=PipelineRunStatus.NOT_STARTED,
        previous_run_id='previousID',
    )
    for field in run:
        # ensure we have a test value to round trip for each field
        assert field

    exec_params = execution_params_from_pipeline_run(run)
    assert run == pipeline_run_from_execution_params(exec_params)

    exec_params_gql = execution_params_from_graphql(exec_params.to_graphql_input())
    assert exec_params_gql == exec_params
    assert run == pipeline_run_from_execution_params(exec_params_gql)

    empty_run = PipelineRun.create_empty_run('foo', 'bar')
    exec_params = execution_params_from_pipeline_run(empty_run)
    assert empty_run == pipeline_run_from_execution_params(exec_params)

    exec_params_gql = execution_params_from_graphql(exec_params.to_graphql_input())
    assert exec_params_gql == exec_params
    assert empty_run == pipeline_run_from_execution_params(exec_params_gql)
