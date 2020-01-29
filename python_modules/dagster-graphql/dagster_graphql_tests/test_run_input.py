from dagster_graphql.client.util import (
    execution_params_from_pipeline_run,
    pipeline_run_from_execution_params,
)

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
    )
    assert run == pipeline_run_from_execution_params(execution_params_from_pipeline_run(run))

    empty_run = PipelineRun.create_empty_run('foo', 'bar')
    assert empty_run == pipeline_run_from_execution_params(
        execution_params_from_pipeline_run(empty_run)
    )
