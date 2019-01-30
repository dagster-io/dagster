import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)
from dagster.core.errors import DagsterUnmarshalInputError
from dagster.core.execution import (
    execute_externalized_plan,
    create_execution_plan,
    ExecutionMetadata,
)
from dagster.core.execution_plan.objects import StepKind
from dagster.core.types.runtime import resolve_to_runtime_type

from dagster.core.types.marshal import serialize_to_file, deserialize_from_file

from dagster.utils.test import get_temp_file_names


def define_inty_pipeline():
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
    return pipeline


def test_basic_pipeline_external_plan_execution():
    pipeline = define_inty_pipeline()

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


def test_external_execution_marshal_wrong_input_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterUnmarshalInputError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'nope': 'nope'}},
            execution_metadata=ExecutionMetadata(),
        )

    assert str(exc_info.value) == 'Input nope does not exist in execution step add_one.transform'
    assert exc_info.value.input_name == 'nope'
    assert exc_info.value.step_key == 'add_one.transform'


def test_external_execution_marshal_code_error():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterUnmarshalInputError) as exc_info:
        execute_externalized_plan(
            pipeline,
            execution_plan,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            execution_metadata=ExecutionMetadata(),
        )

    assert str(exc_info.value) == 'Error during the marshalling of input num'
    assert exc_info.value.input_name == 'num'
    assert exc_info.value.step_key == 'add_one.transform'
