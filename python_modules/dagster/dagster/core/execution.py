'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).

materialize_*

Materializations functions do execution but also allow the user to specify materializations,
which create artifacts that are discoverable by external systems (e.g. files, database
tables, and so on).


'''

# too many lines
# pylint: disable=C0302

from collections import (namedtuple, OrderedDict)
from contextlib import contextmanager
import copy
import sys
import uuid

import six

from dagster import check, config

from dagster.utils.logging import (CompositeLogger, get_formatted_stack_trace)
from dagster.utils.timing import time_execution_scope

from .definitions import (
    SolidDefinition, ExpectationResult, SourceDefinition,
    MaterializationDefinition, PipelineDefinition, PipelineContextDefinition
)

from .errors import (
    DagsterUserCodeExecutionError, DagsterTypeError, DagsterExecutionFailureReason,
    DagsterExpectationFailedError, DagsterInvariantViolationError
)

from .argument_handling import validate_args

Metric = namedtuple('Metric', 'context_dict metric_name value')


class ExecutionContext:
    '''
    A context object flowed through the entire scope of single execution of a
    pipeline of solids. This is used by both framework and user code to log
    messages and metrics. It also maintains a stack of context values so that
    logs, metrics, and any future reporting are reported with a minimal, consistent
    level of context so that developers do not have to repeatedly log well-known
    information (e.g. the name of the solid, the name of the pipeline, etc) when
    logging. Additionally tool author may add their own context values to assist
    reporting.


    resources is an arbitrary user-defined object that can be passed in
    by a user and then access during pipeline execution. This exists so that
    a user does not have to subclass ExecutionContext
    '''

    def __init__(self, loggers=None, resources=None):
        self._logger = CompositeLogger(loggers=loggers)
        self._context_dict = OrderedDict()
        self._metrics = []
        self.resources = resources

    def _maybe_quote(self, val):
        str_val = str(val)
        if ' ' in str_val:
            return '"{val}"'.format(val=str_val)
        return str_val

    def _kv_message(self, extra=None):
        extra = check.opt_dict_param(extra, 'extra')
        return ' '.join(
            [
                '{key}={value}'.format(key=key, value=self._maybe_quote(value))
                for key, value in [*self._context_dict.items(), *extra.items()]
            ]
        )

    def _log(self, method, msg, kwargs):
        check.str_param(method, 'method')
        check.str_param(msg, 'msg')

        check.invariant('extra' not in kwargs, 'do not allow until explicit support is handled')
        check.invariant('exc_info' not in kwargs, 'do not allow until explicit support is handled')

        check.invariant('log_message' not in kwargs, 'log_message_id reserved value')
        check.invariant('log_message_id' not in kwargs, 'log_message_id reserved value')


        full_message = 'message="{message}" {kv_message}'.format(
            message=msg, kv_message=self._kv_message(kwargs)
        )

        log_props = copy.copy(self._context_dict)

        log_props['log_message'] = msg
        log_props['log_message_id'] = str(uuid.uuid4())

        getattr(self._logger, method)(full_message, extra={**log_props, **kwargs})

    def debug(self, msg, **kwargs):
        return self._log('debug', msg, kwargs)

    def info(self, msg, **kwargs):
        return self._log('info', msg, kwargs)

    def warning(self, msg, **kwargs):
        return self._log('warning', msg, kwargs)

    def error(self, msg, **kwargs):
        return self._log('error', msg, kwargs)

    def critical(self, msg, **kwargs):
        return self._log('critical', msg, kwargs)

    # FIXME: Actually make this work
    # def exception(self, e):
    #     check.inst_param(e, 'e', Exception)

    #     # this is pretty lame right. should embellish with more data (stack trace?)
    #     return self._log('error', str(e))

    @contextmanager
    def value(self, key, value):
        check.str_param(key, 'key')
        check.not_none_param(value, 'value')

        check.invariant(not key in self._context_dict, 'Should not be in context')

        self._context_dict[key] = value

        yield

        self._context_dict.pop(key)

    def metric(self, metric_name, value):
        check.str_param(metric_name, 'metric_name')
        check.not_none_param(value, 'value')

        keys = list(self._context_dict.keys())
        keys.append(metric_name)
        if isinstance(value, float):
            format_string = 'metric:{metric_name}={value:.3f} {kv_message}'
        else:
            format_string = 'metric:{metric_name}={value} {kv_message}'

        self._logger.info(
            format_string.format(
                metric_name=metric_name, value=value, kv_message=self._kv_message()
            ),
            extra=self._context_dict
        )

        self._metrics.append(
            Metric(
                context_dict=copy.copy(self._context_dict), metric_name=metric_name, value=value
            )
        )

    def _dict_covers(self, needle_dict, haystack_dict):
        for key, value in needle_dict.items():
            if not key in haystack_dict:
                return False
            if value != haystack_dict[key]:
                return False
        return True

    def metrics_covering_context(self, needle_dict):
        for metric in self._metrics:
            if self._dict_covers(needle_dict, metric.context_dict):
                yield metric

    def metrics_matching_context(self, needle_dict):
        for metric in self._metrics:
            if needle_dict == metric.context_dict:
                yield metric

class DagsterPipelineExecutionResult:
    def __init__(
        self,
        context,
        result_list,
    ):
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=SolidExecutionResult
        )

    @property
    def success(self):
        return all([result.success for result in self.result_list])

    def result_named(self, name):
        check.str_param(name, 'name')
        for result in self.result_list:
            if result.name == name:
                return result
        check.failed('Did not find result {name} in pipeline execution result'.format(name=name))


class SolidExecutionResult:
    '''
    A class to represent the result of the execution of a single solid. Pipeline
    commands return iterators or lists of these results.

    (TODO: explain the various error states)
    '''

    def __init__(
        self,
        success,
        solid,
        transformed_value,
        reason=None,
        exception=None,
        input_expectation_results=None,
        output_expectation_results=None,
        context=None,
    ):
        self.success = check.bool_param(success, 'success')
        if not success:
            check.param_invariant(
                isinstance(reason, DagsterExecutionFailureReason), 'reason',
                'Must provide a reason is result is a failure'
            )
        self.transformed_value = transformed_value
        self.solid = check.inst_param(solid, 'solid', SolidDefinition)
        self.reason = reason
        self.exception = check.opt_inst_param(exception, 'exception', Exception)

        self.input_expectation_results = check.opt_inst_param(
            input_expectation_results,
            'input_expectation_results',
            InputExpectationResults
        )

        self.output_expectation_results = check.opt_inst_param(
            output_expectation_results,
            'output_expectation_results',
            OutputExpectationResults,
        )

        if reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
            check.inst(exception, DagsterUserCodeExecutionError)
            self.user_exception = exception.user_exception
        else:
            self.user_exception = None

        self.context = context

    def reraise_user_error(self):
        check.invariant(self.reason == DagsterExecutionFailureReason.USER_CODE_ERROR)
        check.inst(self.exception, DagsterUserCodeExecutionError)
        six.reraise(*self.exception.original_exc_info)

    @property
    def name(self):
        return self.solid.name

    def copy(self):
        ''' This must be used instead of copy.deepcopy() because exceptions cannot
        be deepcopied'''
        return SolidExecutionResult(
            success=self.success,
            solid=self.solid,
            transformed_value=copy.deepcopy(self.transformed_value),
            context=self.context,
            reason=self.reason,
            exception=self.exception,
            input_expectation_results=self.input_expectation_results.copy()
                    if self.input_expectation_results else None,
            output_expectation_results=self.output_expectation_results.copy()
                    if self.output_expectation_results else None,
        )

def copy_result_list(result_list):
    if result_list is None:
        return result_list

    return [result.copy() for result in result_list]


def copy_result_dict(result_dict):
    if result_dict is None:
        return None
    new_dict = {}
    for input_name, result in result_dict.items():
        new_dict[input_name] = result.copy()
    return new_dict

@contextmanager
def _user_code_error_boundary(context, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the SolidUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.str_param(msg, 'msg')

    try:
        yield
    except Exception as e:
        stack_trace = get_formatted_stack_trace(e)
        context.error(str(e), stack_trace=stack_trace)
        raise DagsterUserCodeExecutionError(
            msg.format(**kwargs), e, user_exception=e, original_exc_info=sys.exc_info()
        )

def _read_source(context, source_definition, arg_dict):
    '''
    Check to ensure that the arguments to a particular input are valid, and then
    execute the input functions. Wraps that execution in appropriate logging, metrics tracking,
    and a user-code error boundary.
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(source_definition, 'source_definition', SourceDefinition)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)

    with context.value('source_type', source_definition.source_type):
        error_context_str = 'source type {source}'.format(source=source_definition.source_type)
        args_to_pass = validate_args(
            source_definition.argument_def_dict,
            arg_dict,
            error_context_str,
        )
        error_str = 'Error occured while loading source "{source_type}"'
        with _user_code_error_boundary(
            context,
            error_str,
            source_type=source_definition.source_type,
        ):
            context.info('Entering input implementation')

            with time_execution_scope() as timer_result:
                value = source_definition.source_fn(context, args_to_pass)

            context.metric('input_load_time_ms', timer_result.millis)

            return value


InputExpectationInfo = namedtuple('InputExpectionInfo', 'solid input_def expectation_def')

def _execute_input_expectation(context, info, value):
    '''
    Execute one user-specified input expectation on an input that has been instantiated in memory
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(info, 'info', InputExpectationInfo)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in input'
    with _user_code_error_boundary(context, error_str, expectation_name=info.expectation_def.name):
        expectation_result = info.expectation_def.expectation_fn(context, info, value)

    if not isinstance(expectation_result, ExpectationResult):
        raise DagsterInvariantViolationError(
            'Must return ExpectationResult from expectation function'
        )
    return expectation_result


OutputExpectationInfo = namedtuple('OutputExpectationInfo', 'solid expectation_def')

def _execute_output_expectation(context, info, transformed_value):
    '''
    Execute one user-specified output expectation on an instantiated result of the core transform.
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', ExecutionContext)
    # check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition)
    check.inst_param(info, 'info', OutputExpectationInfo)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in output'
    expectation_def = info.expectation_def
    with _user_code_error_boundary(context, error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(context, info, transformed_value)

    if not isinstance(expectation_result, ExpectationResult):

        raise DagsterInvariantViolationError(
            'Must return ExpectationResult from expectation function'
        )

    return expectation_result


def _execute_core_transform(context, solid_transform_fn, values_dict):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(values_dict, 'values_dict', key_type=str)

    error_str = 'Error occured during core transform'
    with _user_code_error_boundary(context, error_str):
        with time_execution_scope() as timer_result:
            transformed_value = solid_transform_fn(context, values_dict)

        context.metric('core_transform_time_ms', timer_result.millis)

        return transformed_value


def _execute_materialization(context, materialiation_def, arg_dict, value):
    '''
    Execute a single output, calling into user-specified code. Check validity
    of arguments into the output, do appropriate loggina and metrics tracking, and
    actually execute the output function with an appropriate error boundary.
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(materialiation_def, 'materialization', MaterializationDefinition)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)

    expected_args = set(materialiation_def.argument_def_dict.keys())
    received_args = set(arg_dict.keys())

    if expected_args != received_args:
        raise DagsterTypeError(
            'Argument mismatch in output. Expected {expected} got {received}'.format(
                expected=repr(expected_args),
                received=repr(received_args),
            )
        )

    for arg_name, arg_value in arg_dict.items():
        arg_def_type = materialiation_def.argument_def_dict[arg_name]
        if not arg_def_type.dagster_type.is_python_valid_value(arg_value):
            raise DagsterTypeError(
                'Expected type {typename} for arg {arg_name} in output but got {arg_value}'.format(
                    typename=arg_def_type.dagster_type.name,
                    arg_name=arg_name,
                    arg_value=repr(arg_value),
                )
            )

    error_str = 'Error during execution of materialization'
    with _user_code_error_boundary(context, error_str):
        context.info('Entering materialization implementation')
        materialiation_def.materialization_fn(context, arg_dict, value)


class InputExpectationResult:
    def __init__(self, input_name, all_results):
        self.input_name = check.str_param(input_name, 'input_name')
        self.all_results = check.list_param(all_results, 'all_results', ExpectationResult)

    @property
    def fails(self):
        for result in self.all_results:
            if not result.success:
                yield result

    @property
    def passes(self):
        for result in self.all_results:
            if result.success:
                yield result

    def copy(self):
        return InputExpectationResult(
            input_name=self.input_name,
            all_results=copy_result_list(self.all_results),
        )

class InputExpectationResults:
    def __init__(self, result_dict):
        check.dict_param(
            result_dict,
            'result_dict',
            key_type=str,
            value_type=InputExpectationResult
        )

        all_passes = []
        all_fails = []
        for run_results in result_dict.values():
            all_passes.extend(run_results.passes)
            all_fails.extend(run_results.fails)

        self.all_passes = all_passes
        self.all_fails = all_fails
        self.result_dict = result_dict

    def copy(self):
        return InputExpectationResults(copy_result_dict(self.result_dict))

    @property
    def success(self):
        return not self.all_fails


def _execute_all_input_expectations(context, input_manager, solid, values_dict):
    check.inst_param(context, 'context', ExecutionContext)
    check.dict_param(values_dict, 'values_dict', key_type=str)

    result_dict = {}

    if not input_manager.evaluate_expectations:
        return InputExpectationResults(result_dict)

    for input_name in values_dict.keys():
        input_def = solid.input_def_named(input_name)
        value = values_dict[input_name]

        results = []

        for input_expectation_def in input_def.expectations:
            user_expectation_result = _execute_input_expectation(
                context, InputExpectationInfo(solid, input_def, input_expectation_def), value,
            )
            results.append(user_expectation_result)

        input_result = InputExpectationResult(
            input_name=input_name,
            all_results=results,
        )
        result_dict[input_name] = input_result

    return InputExpectationResults(result_dict)

class OutputExpectationResults:
    def __init__(self, results):
        self.results = check.list_param(results, 'results', ExpectationResult)

    @property
    def success(self):
        for result in self.results:
            if not result.success:
                return False
        return True

    def copy(self):
        return OutputExpectationResults(copy_result_list(self.results))

def _pipeline_solid_in_memory(context, input_manager, solid, transform_values_dict):
    '''
    Given inputs that are already in memory. Evaluation all inputs expectations,
    execute the core transform, and then evaluate all output expectations.

    This is the core of the solid execution that does not touch any extenralized state, whether
    it be inputs or outputs.
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.dict_param(transform_values_dict, 'transform_values_dict', key_type=str)

    input_expectation_results = _execute_all_input_expectations(
        context,
        input_manager,
        solid,
        transform_values_dict
    )

    if not input_expectation_results.success:
        return SolidExecutionResult(
            success=False,
            transformed_value=None,
            solid=solid,
            context=context,
            reason=DagsterExecutionFailureReason.EXPECTATION_FAILURE,
            input_expectation_results=input_expectation_results
        )

    context.info('Executing core transform')

    transformed_value = _execute_core_transform(context, solid.transform_fn, transform_values_dict)

    if not solid.output.dagster_type.is_python_valid_value(transformed_value):
        raise DagsterInvariantViolationError(f'''Solid {solid.name} output {transformed_value}
            which does not match the type for Dagster Type {solid.output.dagster_type.name}''')

    if solid.output.output_callback:
        solid.output.output_callback(context, transformed_value)

    output_expectation_results = _execute_output_expectations(
        context,
        input_manager,
        solid,
        transformed_value,
    )

    if not output_expectation_results.success:
        return SolidExecutionResult(
            success=False,
            transformed_value=None,
            solid=solid,
            context=context,
            reason=DagsterExecutionFailureReason.EXPECTATION_FAILURE,
            input_expectation_results=input_expectation_results,
            output_expectation_results=output_expectation_results,
        )

    return SolidExecutionResult(
        success=True,
        transformed_value=transformed_value,
        solid=solid,
        context=context,
        input_expectation_results=input_expectation_results,
        output_expectation_results=output_expectation_results,
    )


def _execute_output_expectations(context, input_manager, solid, transformed_value):
    if not input_manager.evaluate_expectations:
        return OutputExpectationResults([])

    output_expectation_result_list = []

    for output_expectation_def in solid.output.expectations:
        info = OutputExpectationInfo(solid=solid, expectation_def=output_expectation_def)
        output_expectation_result = _execute_output_expectation(context, info, transformed_value)
        output_expectation_result_list.append(output_expectation_result)

    return OutputExpectationResults(results=output_expectation_result_list)


def _create_passthrough_context_definition(context):
    check.inst_param(context, 'context', ExecutionContext)
    context_definition = PipelineContextDefinition(
        argument_def_dict={},
        context_fn=lambda _pipeline, _args: context
    )
    return {'default': context_definition}


def execute_single_solid(context, solid, environment, throw_on_error=True):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')

    check.invariant(environment.execution.from_solids == [])
    check.invariant(environment.execution.through_solids == [])

    single_solid_environment = config.Environment(
        sources=environment.sources,
        materializations=environment.materializations,
        expectations=environment.expectations,
        context=environment.context,
        execution=config.Execution.single_solid(solid.name),
    )

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid],
            context_definitions=_create_passthrough_context_definition(context),
        ),
        environment=single_solid_environment,
    )

    results = pipeline_result.result_list
    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))
    return results[0]


def _do_throw_on_error(execution_result):
    check.inst_param(execution_result, 'execution_result', SolidExecutionResult)
    if not execution_result.success:
        if execution_result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE:
            raise DagsterExpectationFailedError(execution_result)
        elif execution_result.reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
            execution_result.reraise_user_error()

        check.invariant(execution_result.exception)
        raise execution_result.exception


def output_single_solid(
    context,
    solid,
    environment,
    name,
    arg_dict,
    throw_on_error=True,
):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.str_param(name, 'name')
    check.dict_param(arg_dict, 'arg_dict', key_type=str)
    check.bool_param(throw_on_error, 'throw_on_error')


    results = list(
        execute_pipeline_iterator(
            PipelineDefinition(
                solids=[solid],
                context_definitions=_create_passthrough_context_definition(context),
            ),
            environment=config.Environment(
                context=environment.context,
                sources=environment.sources,
                materializations=[
                    config.Materialization(
                        solid=solid.name, name=name, args=arg_dict
                    )
                ],
            ),
        )
    )

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    if throw_on_error:
        _do_throw_on_error(execution_result)

    return execution_result


def _gather_input_values(context, solid, input_manager):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_manager, 'input_manager', InputManager)

    context.info('About to instantiate and gather all inputs')

    input_values = {}
    for input_def in solid.inputs:
        with context.value('input', input_def.name):
            input_value = input_manager.get_input_value(context, solid, input_def)

            if not input_def.dagster_type.is_python_valid_value(input_value):
                raise DagsterInvariantViolationError(f'''Solid {solid.name} input {input_def.name}
                   received value {input_value} which does not match the type for Dagster type
                   {input_def.dagster_type.name}'''
                )

            input_values[input_def.name] = input_value
            if input_def.input_callback:
                input_def.input_callback(context, input_values[input_def.name])
    return input_values


def _execute_pipeline_solid_step(context, solid, input_manager):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_manager, 'input_manager', InputManager)

    # The value produce by an inputs is potentially different per solid.
    # This is allowed so that two solids that do different instantiation of the
    # same exact input (e.g. the same file) don't have to create additional solids
    # to account for this.

    input_values = _gather_input_values(context, solid, input_manager)

    # This call does all input and output expectations, as well as the core transform
    execution_result = _pipeline_solid_in_memory(context, input_manager, solid, input_values)

    if not execution_result.success:
        return execution_result

    check.invariant(
        solid.name not in input_manager.intermediate_values,
        'should be not in intermediate values'
    )

    transformed_value = execution_result.transformed_value

    context.debug(
        'About to set {output} for {name}'.format(
            output=repr(transformed_value),
            name=solid.name,
        )
    )

    input_manager.intermediate_values[solid.name] = transformed_value

    return SolidExecutionResult(
        success=True,
        solid=solid,
        context=context,
        transformed_value=input_manager.intermediate_values[solid.name],
        input_expectation_results=execution_result.input_expectation_results,
        output_expectation_results=execution_result.output_expectation_results,
        exception=None
    )

class InputManager:
    def __init__(self):
        self.intermediate_values = {}

    @contextmanager
    def yield_context(self):
        check.not_implemented('must implement in subclass')

    @property
    def materializations(self):
        check.not_implemented('must implement in subclass')

    @property
    def evaluate_expectations(self):
        check.not_implemented('must implement in subclass')

    @property
    def from_solids(self):
        check.not_implemented('must implement in subclass')

    @property
    def through_solids(self):
        check.not_implemented('must implement in subclass')

    def get_input_value(self, context, solid, input_def):
        if input_def.depends_on and input_def.depends_on.name in self.intermediate_values:
            # grab value from dependency
            return self.intermediate_values[input_def.depends_on.name]
        else:
            # must get value from source
            return self._get_sourced_input_value(context, solid.name, input_def.name)

    def _get_sourced_input_value(self, _context, _solid_name, _input_name):
        check.not_implemented('must implement in subclass')

def _wrap_in_yield(thing):
    if isinstance(thing, ExecutionContext):
        def _wrap():
            yield thing

        return _wrap()

    return thing


class InMemoryInputManager(InputManager):
    def __init__(self, context, input_values, from_solids=None, through_solids=None):
        super().__init__()
        self.input_values = check.dict_param(input_values, 'input_values', key_type=str)
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self._from_solids = check.opt_list_param(from_solids, from_solids, of_type=str)
        self._through_solids = check.opt_list_param(through_solids, through_solids, of_type=str)

    @property
    def from_solids(self):
        return self._from_solids

    @property
    def through_solids(self):
        return self._through_solids

    def _get_sourced_input_value(self, _context, _solid_name, input_name):
        return self.input_values[input_name]

    @contextmanager
    def yield_context(self):
        return _wrap_in_yield(self.context)

    @property
    def materializations(self):
        return []

    @property
    def evaluate_expectations(self):
        return True

def _validate_environment(environment, pipeline):
    for solid_name, input_configs in environment.sources.items():
        if not pipeline.has_solid(solid_name):
            raise DagsterInvariantViolationError(
                f'Solid "{solid_name} not found'
            )

        solid_inst = pipeline.solid_named(solid_name)

        for input_name, _source_configs in input_configs.items():
            if not solid_inst.has_input(input_name):
                raise DagsterInvariantViolationError(
                    f'Input "{input_name}" not found in the pipeline on solid "{solid_name}".' + \
                    f'Input must be one of {repr(pipeline.input_names)}'
                )

    context_name = environment.context.name

    if context_name not in pipeline.context_definitions:
        avaiable_context_keys = list(pipeline.context_definitions.keys())
        raise DagsterInvariantViolationError(f'Context {context_name} not found in ' + \
            f'pipeline definiton. Available contexts {repr(avaiable_context_keys)}'
        )


class EnvironmentInputManager(InputManager):
    def __init__(self, pipeline, environment):
        super().__init__()
        # This is not necessarily the best spot for these calls
        _validate_environment(environment, pipeline)
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.environment = check.inst_param(environment, 'environment', config.Environment)

    @property
    def from_solids(self):
        return self.environment.execution.from_solids

    @property
    def through_solids(self):
        return self.environment.execution.through_solids

    @contextmanager
    def yield_context(self):
        context_name = self.environment.context.name
        context_definition = self.pipeline.context_definitions[context_name]

        args_to_pass = validate_args(
            self.pipeline.context_definitions[context_name].argument_def_dict,
            self.environment.context.args,
            'pipeline {pipeline_name} context {context_name}'.format(
                pipeline_name=self.pipeline.name,
                context_name=context_name,
            )
        )

        thing = context_definition.context_fn(self.pipeline, args_to_pass)
        return _wrap_in_yield(thing)

    def _get_sourced_input_value(self, context, solid_name, input_name):
        source_config = self.environment.sources[solid_name][input_name]
        input_def = self.pipeline.get_input(solid_name, input_name)
        source_def = input_def.source_of_type(source_config.name)
        return _read_source(
            context, source_def, self.args_for_input(solid_name, input_def.name)
        )

    def args_for_input(self, solid_name, input_name):
        check.str_param(solid_name, 'solid_name')
        check.str_param(input_name, 'input_name')
        return self.environment.sources[solid_name][input_name].args

    @property
    def materializations(self):
        return self.environment.materializations

    @property
    def evaluate_expectations(self):
        return self.environment.expectations.evaluate

def execute_pipeline_iterator(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'enviroment', config.Environment)

    input_manager = EnvironmentInputManager(pipeline, environment)
    with input_manager.yield_context() as context:
        return _execute_pipeline_iterator(
            context,
            pipeline,
            EnvironmentInputManager(pipeline, environment)
        )

def execute_pipeline_iterator_in_memory(
    context,
    pipeline,
    input_values,
    *,
    from_solids=None,
    through_solids=None,
):
    check.opt_list_param(from_solids, 'from_solids', of_type=str)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)
    return _execute_pipeline_iterator(
        context,
        pipeline,
        InMemoryInputManager(context, input_values, from_solids, through_solids),
    )

def _execute_pipeline_iterator(
    context,
    pipeline,
    input_manager,
):
    '''
    This is the core workhorse function of this module, iterating over the pipeline execution
    in topological order. This allow a tool consuming this API to execute a solid one at a time
    and then make decisions based upon the result.

    If you do not specify "through_solids" it executes all the solids specified entire pipeline.
    If through_solids is specified, it will stop executing once all of those solids in
    through_solids have been executed.

    If you want to actually output the results of the transform see output_pipeline_iterator

    execute_pipeline is the "synchronous" version of this function and returns a list of results
    once the entire pipeline has been executed.
    '''

    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(input_manager, 'input_manager', InputManager)

    through_solids = input_manager.through_solids
    from_solids = input_manager.from_solids

    pipeline_context_value = pipeline.name if pipeline.name else 'unnamed'

    materialization_args = MaterializationArgs(pipeline, input_manager.materializations)

    if through_solids is None:
        through_solids = materialization_args.through_solids

    with context.value('pipeline', pipeline_context_value):
        input_manager = input_manager

        if not through_solids:
            through_solids = pipeline.all_sink_solids

        if not from_solids:
            all_deps = set()
            for through_solid in through_solids:
                all_deps.union(pipeline.solid_graph.transitive_dependencies_of(through_solid))

            from_solids = list(all_deps)

        # TODO provide meaningful error messages when the wrong inputs are provided for a particular
        # execution subgraph

        # for through_solid_name in through_solids:
        #     unprovided_inputs = pipeline.solid_graph.compute_unprovided_inputs(
        #         input_names=sourced_input_names, solid_name=through_solid_name
        #     )
        #     if unprovided_inputs:
        #         check.failed(
        #             'Failed to provide inputs {unprovided_inputs} for solid {name}'.format(
        #                 unprovided_inputs=unprovided_inputs, name=through_solid_name
        #             )
        #         )

        execution_graph = pipeline.solid_graph.create_execution_subgraph(
            from_solids, list(through_solids)
        )

        for solid in execution_graph.topological_solids:

            try:
                with context.value('solid', solid.name):
                    result = _execute_pipeline_solid_step(context, solid, input_manager)

                    if not result.success:
                        yield result
                        break

                    if not materialization_args.should_materialize(result.name):
                        yield result
                        continue

                    _execute_materializations(
                        context,
                        solid,
                        materialization_args.materializations_for_solid(solid.name),
                        result.transformed_value,
                    )

                    yield result

            except DagsterUserCodeExecutionError as see:
                yield SolidExecutionResult(
                    success=False,
                    reason=DagsterExecutionFailureReason.USER_CODE_ERROR,
                    solid=solid,
                    context=context,
                    transformed_value=None,
                    exception=see,
                )
                break

def _execute_materializations(
    context,
    solid,
    materializations,
    transformed_value,
):
    for materialization in materializations:
        arg_dict = materialization.args
        name = materialization.name
        with context.value('materialization_name', name):
            mat_def = solid.output.materialization_of_type(name)
            _execute_materialization(context, mat_def, arg_dict, transformed_value)

def execute_pipeline(
    pipeline,
    environment,
    *,
    throw_on_error=True,
):
    check.inst_param(environment, 'environment', config.Environment)
    return _execute_pipeline(
        pipeline,
        EnvironmentInputManager(pipeline, environment),
        throw_on_error,
    )

def execute_pipeline_in_memory(
    context,
    pipeline,
    *,
    input_values,
    from_solids=None,
    through_solids=None,
    throw_on_error=True,
):
    check.dict_param(input_values, 'input_values', key_type=str)
    return _execute_pipeline(
        pipeline,
        InMemoryInputManager(context, input_values, from_solids, through_solids),
        throw_on_error,
    )

def _execute_pipeline(
    pipeline,
    input_manager,
    throw_on_error=True,
):
    '''
    "Synchronous" version of execute_pipeline_iteator.

    throw_on_error makes the function throw when an error is encoutered rather than returning
    the SolidExecutionResult in an error-state.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(input_manager, 'input_manager', InputManager)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = []
    with input_manager.yield_context() as context:
        for result in _execute_pipeline_iterator(
            context,
            pipeline,
            input_manager=input_manager,
        ):
            if throw_on_error:
                if not result.success:
                    _do_throw_on_error(result)

            results.append(result.copy())
        return DagsterPipelineExecutionResult(context, results)


class MaterializationArgs:
    def __init__(self, pipeline, materializations):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(materializations, 'materializations', of_type=config.Materialization)

        self.pipeline = pipeline
        self.materializations = list(materializations)
        self.through_solids = [materialization.solid for materialization in self.materializations]

    def should_materialize(self, solid_name):
        return solid_name in self.through_solids

    def materializations_for_solid(self, solid_name):
        for materialization in self.materializations:
            if materialization.solid == solid_name:
                yield materialization
