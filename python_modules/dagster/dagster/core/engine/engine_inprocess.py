import os
import sys

from dagster import EventMetadataEntry, check
from dagster.core.definitions import ExpectationResult, Materialization, Output, TypeCheck
from dagster.core.errors import (
    DagsterError,
    DagsterExecutionStepExecutionError,
    DagsterInputHydrationConfigError,
    DagsterInvariantViolationError,
    DagsterOutputMaterializationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.compute_logs import mirror_step_io
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)
from dagster.core.execution.memoization import copy_required_intermediates_for_execution
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
)
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.storage.object_store import ObjectStoreOperation
from dagster.core.types.dagster_type import DagsterType
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.timing import format_duration, time_execution_scope

from .engine_base import Engine


class InProcessEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Executing steps in process (pid: {pid})'.format(pid=os.getpid()),
            event_specific_data=EngineEventData.in_process(
                os.getpid(), execution_plan.step_keys_to_execute
            ),
        )

        with time_execution_scope() as timer_result:
            check.param_invariant(
                isinstance(pipeline_context.executor_config, ExecutorConfig),
                'pipeline_context',
                'Expected executor_config to be ExecutorConfig got {}'.format(
                    pipeline_context.executor_config
                ),
            )

            for event in copy_required_intermediates_for_execution(
                pipeline_context, execution_plan
            ):
                yield event

            # It would be good to implement a reference tracking algorithm here to
            # garbage collect results that are no longer needed by any steps
            # https://github.com/dagster-io/dagster/issues/811
            active_execution = execution_plan.start()
            while not active_execution.is_complete:

                steps = active_execution.get_steps_to_execute(limit=1)
                check.invariant(
                    len(steps) == 1, 'Invariant Violation: expected step to be available to execute'
                )
                step = steps[0]
                step_context = pipeline_context.for_step(step)
                check.invariant(
                    all(
                        hasattr(step_context.resources, resource_key)
                        for resource_key in step_context.required_resource_keys
                    ),
                    'expected step context to have all required resources',
                )

                with mirror_step_io(step_context):
                    # capture all of the logs for this step
                    uncovered_inputs = pipeline_context.intermediates_manager.uncovered_inputs(
                        step_context, step
                    )
                    if uncovered_inputs:
                        # In partial pipeline execution, we may end up here without having validated the
                        # missing dependent outputs were optional
                        _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step.key)

                        step_context.log.info(
                            (
                                'Not all inputs covered for {step}. Not executing. Output missing for '
                                'inputs: {uncovered_inputs}'
                            ).format(uncovered_inputs=uncovered_inputs, step=step.key)
                        )
                        yield DagsterEvent.step_skipped_event(step_context)
                        active_execution.mark_skipped(step.key)
                        continue

                    step_success = None
                    for step_event in check.generator(
                        dagster_event_sequence_for_step(step_context)
                    ):
                        check.inst(step_event, DagsterEvent)
                        yield step_event

                        if step_event.is_step_failure:
                            step_success = False
                        elif step_event.is_step_success:
                            step_success = True

                    if step_success == True:
                        active_execution.mark_success(step.key)
                    elif step_success == False:
                        active_execution.mark_failed(step.key)
                    else:
                        pipeline_context.log.error(
                            'Step {key} finished without success or failure event, assuming failure.'.format(
                                key=step.key
                            )
                        )
                        active_execution.mark_failed(step.key)

                # process skips from failures or uncovered inputs
                for event in active_execution.skipped_step_events_iterator(pipeline_context):
                    yield event

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Finished steps in process (pid: {pid}) in {duration_ms}'.format(
                pid=os.getpid(), duration_ms=format_duration(timer_result.millis)
            ),
            event_specific_data=EngineEventData.in_process(
                os.getpid(), execution_plan.step_keys_to_execute
            ),
        )


def _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step_key):
    nonoptionals = [
        handle for handle in uncovered_inputs if not execution_plan.get_step_output(handle).optional
    ]
    if nonoptionals:
        raise DagsterStepOutputNotFoundError(
            (
                'When executing {step} discovered required outputs missing '
                'from previous step: {nonoptionals}'
            ).format(nonoptionals=nonoptionals, step=step_key),
            step_key=nonoptionals[0].step_key,
            output_name=nonoptionals[0].output_name,
        )


class MultipleStepOutputsListWrapper(list):
    pass


def _input_values_from_intermediates_manager(step_context):
    step = step_context.step

    input_values = {}
    for step_input in step.step_inputs:
        if step_input.runtime_type.is_nothing:
            continue

        if step_input.is_from_multiple_outputs:
            if hasattr(step_input.runtime_type, 'inner_type'):
                runtime_type = step_input.runtime_type.inner_type
            else:  # This is the case where the fan-in is typed Any
                runtime_type = step_input.runtime_type
            _input_value = [
                step_context.intermediates_manager.get_intermediate(
                    step_context, runtime_type, source_handle
                )
                for source_handle in step_input.source_handles
            ]
            # When we're using an object store-backed intermediate store, we wrap the
            # ObjectStoreOperation[] representing the fan-in values in a MultipleStepOutputsListWrapper
            # so we can yield the relevant object store events and unpack the values in the caller
            if all((isinstance(x, ObjectStoreOperation) for x in _input_value)):
                input_value = MultipleStepOutputsListWrapper(_input_value)
            else:
                input_value = _input_value

        elif step_input.is_from_single_output:
            input_value = step_context.intermediates_manager.get_intermediate(
                step_context, step_input.runtime_type, step_input.source_handles[0]
            )

        else:  # is from config

            def _generate_error_boundary_msg_for_step_input(_context, _input):
                return lambda: '''Error occured during input hydration:
                input name: "{input}"
                step key: "{key}"
                solid invocation: "{solid}"
                solid definition: "{solid_def}"
                '''.format(
                    input=_input.name,
                    key=_context.step.key,
                    solid_def=_context.solid_def.name,
                    solid=_context.solid.name,
                )

            with user_code_error_boundary(
                DagsterInputHydrationConfigError,
                msg_fn=_generate_error_boundary_msg_for_step_input(step_context, step_input),
            ):
                input_value = step_input.runtime_type.input_hydration_config.construct_from_config_value(
                    step_context, step_input.config_data
                )
        input_values[step_input.name] = input_value

    return input_values


def _step_failure_event_from_exc_info(step_context, exc_info, user_failure_data=None):
    return DagsterEvent.step_failure_event(
        step_context=step_context,
        step_failure_data=StepFailureData(
            error=serializable_error_info_from_exc_info(exc_info),
            user_failure_data=user_failure_data,
        ),
    )


def dagster_event_sequence_for_step(step_context):
    '''
    Yield a sequence of dagster events for the given step with the step context.

    Thie function also processes errors. It handles a few error cases:

        (1) The user-space code has raised an Exception. It has been
        wrapped in an exception derived from DagsterUserCodeException. In that
        case the original user exc_info is stashed on the exception
        as the original_exc_info property. Examples of this are computations
        with the compute_fn, and type checks. If the user has raised an
        intentional error via throwing Failure, they can also optionally
        pass along explicit metadata attached to that Failure.

        (2) The framework raised a DagsterError that indicates a usage error
        or some other error not communicated by a user-thrown exception. For example,
        if the user yields an object out of a compute function that is not a
        proper event (not an Output, ExpectationResult, etc).

        (3) An unexpected error occured. This is a framework error. Either there
        has been an internal error in the framewore OR we have forgtten to put a
        user code error boundary around invoked user-space code. These terminate
        the computation immediately (by re-raising).

    The "raised_dagster_errors" context manager can be used to force these errors to be
    reraised and surfaced to the user. This is mostly to get sensible errors in test and
    ad-hoc contexts, rather than forcing the user to wade through the
    PipelineExecutionResult API in order to find the step that errored.

    For tools, however, this option should be false, and a sensible error message
    signaled to the user within that tool.
    '''

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    try:
        for step_event in check.generator(_core_dagster_event_sequence_for_step(step_context)):
            yield step_event

    # case (1) in top comment
    except DagsterUserCodeExecutionError as dagster_user_error:  # case (1) above
        yield _step_failure_event_from_exc_info(
            step_context,
            dagster_user_error.original_exc_info,
            UserFailureData(
                label='intentional-failure',
                description=dagster_user_error.user_specified_failure.description,
                metadata_entries=dagster_user_error.user_specified_failure.metadata_entries,
            )
            if dagster_user_error.is_user_specified_failure
            else None,
        )

        if step_context.raise_on_error:
            raise dagster_user_error.user_exception

    # case (2) in top comment
    except DagsterError as dagster_error:
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        if step_context.raise_on_error:
            raise dagster_error

    # case (3) in top comment
    except (Exception, KeyboardInterrupt) as unexpected_exception:  # pylint: disable=broad-except
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        raise unexpected_exception


def _step_output_error_checked_user_event_sequence(step_context, user_event_sequence):
    '''
    Process the event sequence to check for invariant violations in the event
    sequence related to Output events emitted from the compute_fn.

    This consumes and emits an event sequence.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.generator_param(user_event_sequence, 'user_event_sequence')

    step = step_context.step
    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs = set()

    for user_event in user_event_sequence:
        if not isinstance(user_event, Output):
            yield user_event
            continue

        # do additional processing on Outputs
        output = user_event
        if not step.has_step_output(output.output_name):
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{output.output_name}" that does not exist. The available '
                'outputs are {output_names}'.format(
                    handle=str(step.solid_handle), output=output, output_names=output_names
                )
            )

        if output.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{output.output_name}" multiple times'.format(
                    handle=str(step.solid_handle), output=output
                )
            )

        yield output
        seen_outputs.add(output.output_name)

    for step_output_def in step.step_outputs:
        if not step_output_def.name in seen_outputs and not step_output_def.optional:
            if step_output_def.runtime_type.is_nothing:
                step_context.log.info(
                    'Emitting implicit Nothing for output "{output}" on solid {solid}'.format(
                        output=step_output_def.name, solid={str(step.solid_handle)}
                    )
                )
                yield Output(output_name=step_output_def.name, value=None)
            else:
                raise DagsterStepOutputNotFoundError(
                    'Core compute for solid "{handle}" did not return an output '
                    'for non-optional output "{step_output_def.name}"'.format(
                        handle=str(step.solid_handle), step_output_def=step_output_def
                    ),
                    step_key=step.key,
                    output_name=step_output_def.name,
                )


class DagsterTypeCheckDidNotPass(DagsterError):
    """
    Raised when:

    1. raise_on_error is True in calls to execute_pipeline, execute_solid and similar.
    2. When a DagsterType's type check fails by returning False or TypeCheck with success=False.
    """

    def __init__(self, description=None, metadata_entries=None, dagster_type=None):
        super(DagsterTypeCheckDidNotPass, self).__init__(description)
        self.description = check.opt_str_param(description, 'description')
        self.metadata_entries = check.opt_list_param(
            metadata_entries, 'metadata_entries', of_type=EventMetadataEntry
        )
        self.dagster_type = check.opt_inst_param(dagster_type, 'dagster_type', DagsterType)


def _do_type_check(context, runtime_type, value):
    type_check = runtime_type.type_check(context, value)
    if not isinstance(type_check, TypeCheck):
        return TypeCheck(
            success=False,
            description=(
                'Type checks must return TypeCheck. Type check for type {type_name} returned '
                'value of type {return_type} when checking runtime value of type {runtime_type}.'
            ).format(
                type_name=runtime_type.name, return_type=type(type_check), runtime_type=type(value)
            ),
        )
    return type_check


def _create_step_input_event(step_context, input_name, type_check, success):
    return DagsterEvent.step_input_event(
        step_context,
        StepInputData(
            input_name=input_name,
            type_check_data=TypeCheckData(
                success=success,
                label=input_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
        ),
    )


def _type_checked_event_sequence_for_input(step_context, input_name, input_value):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.str_param(input_name, 'input_name')

    step_input = step_context.step.step_input_named(input_name)
    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            'In solid "{handle}" the input "{input_name}" received '
            'value {input_value} of Python type {input_type} which '
            'does not pass the typecheck for Dagster type '
            '{dagster_type_name}. Step {step_key}.'
        ).format(
            handle=str(step_context.step.solid_handle),
            input_name=input_name,
            input_value=input_value,
            input_type=type(input_value),
            dagster_type_name=step_input.runtime_type.name,
            step_key=step_context.step.key,
        ),
    ):
        type_check = _do_type_check(
            step_context.for_type(step_input.runtime_type), step_input.runtime_type, input_value,
        )

        yield _create_step_input_event(
            step_context, input_name, type_check=type_check, success=type_check.success
        )

        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description='Type check failed for step input {input_name} of type {runtime_type}.'.format(
                    input_name=input_name, runtime_type=step_input.runtime_type.name,
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=step_input.runtime_type,
            )


def _create_step_output_event(step_context, output, type_check, success):
    return DagsterEvent.step_output_event(
        step_context=step_context,
        step_output_data=StepOutputData(
            step_output_handle=StepOutputHandle.from_step(
                step=step_context.step, output_name=output.output_name
            ),
            type_check_data=TypeCheckData(
                success=success,
                label=output.output_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
        ),
    )


def _type_checked_step_output_event_sequence(step_context, output):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(output, 'output', Output)

    step_output = step_context.step.step_output_named(output.output_name)
    with user_code_error_boundary(
        DagsterTypeCheckError,
        lambda: (
            'In solid "{handle}" the output "{output_name}" received '
            'value {output_value} of Python type {output_type} which '
            'does not pass the typecheck for Dagster type '
            '{dagster_type_name}. Step {step_key}.'
        ).format(
            handle=str(step_context.step.solid_handle),
            output_name=output.output_name,
            output_value=output.value,
            output_type=type(output.value),
            dagster_type_name=step_output.runtime_type.name,
            step_key=step_context.step.key,
        ),
    ):
        type_check = _do_type_check(
            step_context.for_type(step_output.runtime_type), step_output.runtime_type, output.value
        )

        yield _create_step_output_event(
            step_context, output, type_check=type_check, success=type_check.success
        )

        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description='Type check failed for step output {output_name} of type {runtime_type}.'.format(
                    output_name=output.output_name, runtime_type=step_output.runtime_type.name,
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=step_output.runtime_type,
            )


def _core_dagster_event_sequence_for_step(step_context):
    '''
    Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    yield DagsterEvent.step_start_event(step_context)

    inputs = {}
    for input_name, input_value in _input_values_from_intermediates_manager(step_context).items():
        if isinstance(input_value, ObjectStoreOperation):
            yield DagsterEvent.object_store_operation(
                step_context, ObjectStoreOperation.serializable(input_value, value_name=input_name)
            )
            inputs[input_name] = input_value.obj
        elif isinstance(input_value, MultipleStepOutputsListWrapper):
            for op in input_value:
                yield DagsterEvent.object_store_operation(
                    step_context, ObjectStoreOperation.serializable(op, value_name=input_name)
                )
            inputs[input_name] = [op.obj for op in input_value]
        else:
            inputs[input_name] = input_value

    for input_name, input_value in inputs.items():
        for evt in check.generator(
            _type_checked_event_sequence_for_input(step_context, input_name, input_value)
        ):
            yield evt

    with time_execution_scope() as timer_result:
        user_event_sequence = check.generator(
            _user_event_sequence_for_step_compute_fn(step_context, inputs)
        )

        # It is important for this loop to be indented within the
        # timer block above in order for time to be recorded accurately.
        for user_event in check.generator(
            _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
        ):

            if isinstance(user_event, Output):
                for evt in _create_step_events_for_output(step_context, user_event):
                    yield evt
            elif isinstance(user_event, Materialization):
                yield DagsterEvent.step_materialization(step_context, user_event)
            elif isinstance(user_event, ExpectationResult):
                yield DagsterEvent.step_expectation_result(step_context, user_event)
            else:
                check.failed(
                    'Unexpected event {event}, should have been caught earlier'.format(
                        event=user_event
                    )
                )

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _create_step_events_for_output(step_context, output):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(output, 'output', Output)

    step = step_context.step
    step_output = step.step_output_named(output.output_name)

    for output_event in _type_checked_step_output_event_sequence(step_context, output):
        yield output_event

    step_output_handle = StepOutputHandle.from_step(step=step, output_name=output.output_name)

    for evt in _set_intermediates(step_context, step_output, step_output_handle, output):
        yield evt

    for evt in _create_output_materializations(step_context, output.output_name, output.value):
        yield evt


def _set_intermediates(step_context, step_output, step_output_handle, output):
    res = step_context.intermediates_manager.set_intermediate(
        context=step_context,
        runtime_type=step_output.runtime_type,
        step_output_handle=step_output_handle,
        value=output.value,
    )
    if isinstance(res, ObjectStoreOperation):
        yield DagsterEvent.object_store_operation(
            step_context, ObjectStoreOperation.serializable(res, value_name=output.output_name)
        )


def _create_output_materializations(step_context, output_name, value):
    step = step_context.step
    current_handle = step.solid_handle

    # check for output mappings at every point up the composition heirarchy
    while current_handle:
        solid_config = step_context.environment_config.solids.get(current_handle.to_string())
        current_handle = current_handle.parent

        if solid_config is None:
            continue

        for output_spec in solid_config.outputs:
            check.invariant(len(output_spec) == 1)
            config_output_name, output_spec = list(output_spec.items())[0]
            if config_output_name == output_name:
                step_output = step.step_output_named(output_name)
                with user_code_error_boundary(
                    DagsterOutputMaterializationError,
                    msg_fn=lambda: '''Error occured during output materialization:
                    output name: "{output_name}"
                    step key: "{key}"
                    solid invocation: "{solid}"
                    solid definition: "{solid_def}"
                    '''.format(
                        output_name=output_name,
                        key=step_context.step.key,
                        solid_def=step_context.solid_def.name,
                        solid=step_context.solid.name,
                    ),
                ):
                    materialization = step_output.runtime_type.output_materialization_config.materialize_runtime_value(
                        step_context, output_spec, value
                    )

                if not isinstance(materialization, Materialization):
                    raise DagsterInvariantViolationError(
                        (
                            'materialize_runtime_value on type {type_name} has returned '
                            'value {value} of type {python_type}. You must return a '
                            'Materialization.'
                        ).format(
                            type_name=step_output.runtime_type.name,
                            value=repr(materialization),
                            python_type=type(materialization).__name__,
                        )
                    )

                yield DagsterEvent.step_materialization(step_context, materialization)


def _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    with user_code_error_boundary(
        DagsterExecutionStepExecutionError,
        msg_fn=lambda: '''Error occured during the execution of step:
        step key: "{key}"
        solid invocation: "{solid}"
        solid definition: "{solid_def}"
        '''.format(
            key=step_context.step.key,
            solid_def=step_context.solid_def.name,
            solid=step_context.solid.name,
        ),
        step_key=step_context.step.key,
        solid_def_name=step_context.solid_def.name,
        solid_name=step_context.solid.name,
    ):

        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for event in gen:
                yield event
