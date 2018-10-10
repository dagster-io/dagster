from dagster import (
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    types,
)


@lambda_solid
def return_one():
    return 1


class Some(object):
    def __init__(self, value):
        self.value = value


SomeType = types.PythonObjectType('SomeType', Some)


def test_serialize_one_int():

    pipeline_def = PipelineDefinition(solids=[return_one])
    result = execute_pipeline(pipeline_def, {'execution': {'serialize_intermediates': True}})
    assert result.success
    path = '/tmp/dagster/runs/{run_id}/return_one/outputs/result'.format(run_id=result.run_id)
    value = types.Any.deserialize_value(path)
    assert value == 1


@lambda_solid(output=OutputDefinition(SomeType))
def return_some_type():
    return Some('foobar')


def test_serialize_custom_type():

    pipeline_def = PipelineDefinition(solids=[return_some_type])
    result = execute_pipeline(pipeline_def, {'execution': {'serialize_intermediates': True}})
    assert result.success
    path = '/tmp/dagster/runs/{run_id}/return_some_type/outputs/result'.format(run_id=result.run_id)
    some = SomeType.deserialize_value(path)
    assert some.value == 'foobar'
