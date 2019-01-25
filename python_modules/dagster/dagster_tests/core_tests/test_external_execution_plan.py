from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)
from dagster.core.execution import execute_externalized_plan
from dagster.core.execution_plan.objects import StepTag
from dagster.core.types.runtime import resolve_to_runtime_type

from dagster.utils.test import get_temp_file_names


def test_basic_pipeline_external_plan_execution():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solids=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    with get_temp_file_names(2) as temp_files:

        temp_path, write_path = temp_files  # pylint: disable=W0632

        int_type = resolve_to_runtime_type(Int)

        int_type.marshalling_strategy.marshal_value(5, temp_path)

        results = execute_externalized_plan(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': temp_path}},
            outputs_to_marshal={'add_one.transform': [{'output': 'result', 'path': write_path}]},
        )

        assert int_type.marshalling_strategy.unmarshal_value(write_path) == 6

    assert len(results) == 2

    thunk_step_result = results[0]

    assert thunk_step_result.tag == StepTag.VALUE_THUNK

    transform_step_result = results[1]
    assert transform_step_result.tag == StepTag.TRANSFORM
    assert transform_step_result.success
    assert transform_step_result.success_data.output_name == 'result'
    assert transform_step_result.success_data.value == 6
