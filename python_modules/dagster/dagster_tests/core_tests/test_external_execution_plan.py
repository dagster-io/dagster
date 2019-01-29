from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)
from dagster.core.execution import (
    execute_externalized_plan,
    create_execution_plan,
    ExecutionMetadata,
)
from dagster.core.execution_plan.objects import StepKind
from dagster.core.types.runtime import resolve_to_runtime_type

from dagster.core.types.marshal import serialize_to_file, deserialize_from_file

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

        serialize_to_file(int_type.serialization_strategy, 5, temp_path)

        execution_plan = create_execution_plan(pipeline)

        results = execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': temp_path}},
            outputs_to_marshal={'add_one.transform': [{'output': 'result', 'path': write_path}]},
            execution_metadata=ExecutionMetadata(),
        )

        assert deserialize_from_file(int_type.serialization_strategy, write_path) == 6

    assert len(results) == 2

    thunk_step_result = results[0]

    assert thunk_step_result.kind == StepKind.VALUE_THUNK

    transform_step_result = results[1]
    assert transform_step_result.kind == StepKind.TRANSFORM
    assert transform_step_result.success
    assert transform_step_result.success_data.output_name == 'result'
    assert transform_step_result.success_data.value == 6
