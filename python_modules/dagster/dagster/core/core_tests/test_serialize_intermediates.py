from dagster import (
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    types,
)


@lambda_solid
def return_one():
    return 1


def test_serialize_one_int():

    pipeline_def = PipelineDefinition(solids=[return_one])
    result = execute_pipeline(pipeline_def, {'execution': {'serialize_intermediates': True}})
    assert result.success
    path = '/tmp/dagster/runs/{run_id}/return_one/outputs/result'.format(run_id=result.run_id)
    value = types.Any.deserialize_value(path)
    assert value == 1
