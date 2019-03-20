import uuid
import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    lambda_solid,
)

from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvalidSubplanInputNotFoundError,
    DagsterInvalidSubplanMissingInputError,
    DagsterInvalidSubplanOutputNotFoundError,
)

from dagster.core.execute_marshalling import execute_marshalling, MarshalledOutput
from dagster.core.object_store import FileSystemObjectStore
from dagster.core.execution import (
    ExecutionStepEventType,
    create_execution_plan,
    execute_plan_subset,
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

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solids=[return_one, add_one, user_throw_exception],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    return pipeline


def test_basic_pipeline_external_plan_execution():
    pipeline = define_inty_pipeline()

    with get_temp_file_names(2) as temp_files:

        temp_path, write_path = temp_files  # pylint: disable=W0632

        int_type = resolve_to_runtime_type(Int)

        serialize_to_file(int_type.serialization_strategy, 5, temp_path)

        step_events = execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': temp_path}},
            outputs_to_marshal={'add_one.transform': [MarshalledOutput('result', write_path)]},
        )

        assert deserialize_from_file(int_type.serialization_strategy, write_path) == 6

    assert len(step_events) == 1

    transform_step_output_event = step_events[0]
    assert transform_step_output_event.step_kind == StepKind.TRANSFORM
    assert transform_step_output_event.is_successful_output
    assert transform_step_output_event.step_output_data.output_name == 'result'
    assert transform_step_output_event.step_output_data.get_value() == 6


def test_external_execution_marshal_wrong_input_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanInputNotFoundError) as exc_info:
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'nope': 'nope'}},
        )

    assert str(exc_info.value) == 'Input nope on add_one.transform does not exist.'
    assert exc_info.value.pipeline_name == pipeline.name
    assert exc_info.value.step_keys == ['add_one.transform']


def test_external_execution_step_for_input_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_marshalling(
            pipeline, ['add_one.transform'], inputs_to_marshal={'nope': {'nope': 'nope'}}
        )

    assert exc_info.value.step_key == 'nope'


def test_external_execution_input_marshal_code_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(IOError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
        )

    # This throws outside of the normal execution process for now so this is expected
    with pytest.raises(IOError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            run_config=RunConfig.nonthrowing_in_process(),
        )


def test_external_execution_step_for_output_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            inputs_to_marshal={'add_one.transform': {'num': 'nope'}},
            outputs_to_marshal={'nope': [MarshalledOutput('nope', 'nope')]},
        )


def test_external_execution_output_missing():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanOutputNotFoundError):
        execute_marshalling(
            pipeline,
            ['add_one.transform'],
            outputs_to_marshal={'add_one.transform': [MarshalledOutput('nope', 'nope')]},
        )


def test_external_execution_marshal_output_code_error():
    pipeline = define_inty_pipeline()

    # guaranteed that folder does not exist
    hardcoded_uuid = '83fb4ace-5cab-459d-99b6-2ca9808c54a1'

    outputs_to_marshal = {
        'add_one.transform': [
            MarshalledOutput(
                output_name='result', marshalling_key='{uuid}/{uuid}'.format(uuid=hardcoded_uuid)
            )
        ]
    }

    with pytest.raises(IOError) as exc_info:
        execute_marshalling(
            pipeline,
            ['return_one.transform', 'add_one.transform'],
            outputs_to_marshal=outputs_to_marshal,
        )

    assert 'No such file or directory' in str(exc_info.value)

    # This throws outside of the normal execution process for now so this is expected
    with pytest.raises(IOError) as exc_info:
        execute_marshalling(
            pipeline,
            ['return_one.transform', 'add_one.transform'],
            outputs_to_marshal=outputs_to_marshal,
            run_config=RunConfig.nonthrowing_in_process(),
        )


def test_external_execution_output_code_error_throw_on_user_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(Exception) as exc_info:
        execute_marshalling(pipeline, ['user_throw_exception.transform'])

    assert str(exc_info.value) == 'whoops'


def test_external_execution_output_code_error_no_throw_on_user_error():
    pipeline = define_inty_pipeline()

    step_events = execute_marshalling(
        pipeline, ['user_throw_exception.transform'], run_config=RunConfig.nonthrowing_in_process()
    )

    assert len(step_events) == 1
    step_event = step_events[0]
    assert step_event.step_failure_data
    assert step_event.step_failure_data.error_cls_name == 'Exception'
    assert step_event.step_failure_data.error_message == 'Exception: whoops\n'


def test_external_execution_unsatisfied_input_error():
    pipeline = define_inty_pipeline()

    with pytest.raises(DagsterInvalidSubplanMissingInputError) as exc_info:
        execute_marshalling(pipeline, ['add_one.transform'])

    assert exc_info.value.pipeline_name == 'basic_external_plan_execution'
    assert exc_info.value.step_keys == ['add_one.transform']
    assert exc_info.value.step.key == 'add_one.transform'
    assert exc_info.value.input_name == 'num'

    assert str(exc_info.value) == (
        "You have specified a subset execution on pipeline basic_external_plan_execution with "
        "step_keys ['add_one.transform']. You have failed to provide the required input num for "
        "step add_one.transform."
    )


def get_step_output(step_events, step_key, output_name='result'):
    for step_event in step_events:
        if (
            step_event.event_type == ExecutionStepEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


# This should go away with https://github.com/dagster-io/dagster/issues/953
def has_output_value(run_id, step_key, output_name='result'):
    paths = ['intermediates', step_key, output_name]
    object_store = FileSystemObjectStore(run_id)
    return object_store.has_object(context=None, paths=paths)


# This should go away with https://github.com/dagster-io/dagster/issues/953
def get_output_value(run_id, step_key, runtime_type, output_name='result'):
    object_store = FileSystemObjectStore(run_id)
    paths = ['intermediates', step_key, output_name]
    return object_store.get_object(context=None, runtime_type=runtime_type, paths=paths)


def test_using_file_system_for_subplan():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)

    assert execution_plan.get_step_by_key('return_one.transform')

    step_keys = ['return_one.transform']

    run_id = str(uuid.uuid4())

    return_one_step_events = list(
        execute_plan_subset(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=step_keys,
        )
    )

    assert get_step_output(return_one_step_events, 'return_one.transform')
    assert has_output_value(run_id, 'return_one.transform')
    assert get_output_value(run_id, 'return_one.transform', Int) == 1

    add_one_step_events = list(
        execute_plan_subset(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=['add_one.transform'],
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.transform')
    assert has_output_value(run_id, 'add_one.transform')
    assert get_output_value(run_id, 'add_one.transform', Int) == 2
