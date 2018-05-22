'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).

output_*

Output functions do execution but also allow the user to specify outputs, which create artifacts
that are discoverable by external systems (e.g. files, database tables, and so on).

Argument conventions across the file:

input_arg_dicts: {string : { string: string } }

A dictionary of dictionarys. The first level is indexed by input *name*. Put an entry for each
input you want to specify. Each one of inputs in turn has an argumect dictionary, which is just
a set of key value pairs, represented by a bare python dictionary:

So for example a solid that takes two csv inputs would have the input_arg_dicts:

{
    "csv_one" : { "path" : "path/to/csv_one.csv},
    "csv_two" : { "path" : "path/to/csv_two.csv},
}

output_arg_dicts : { string : string : string : string } } }

A dictionary of dictionary of dictionarys.

The first level is a solid nane. These are the solids where the user wants to output something.

The next level is the output name. This level allows the user to specify multiple outputs per solid.

Lastly is the arg_dict for that output in that solid

Example where you want to output a csv for a single solid:

{
    "some_solid" {
        "CSV" : {
            "path" : "path/to/an/output.csv"
        }
    }
}
'''
from collections import (namedtuple, OrderedDict)
from contextlib import contextmanager
import copy
import sys

import six

from dagster import check

from dagster.utils.logging import (CompositeLogger, ERROR)
from dagster.utils.timing import time_execution_scope

from .definitions import (
    Solid,
    SolidInputDefinition,
    SolidOutputDefinition,
    SolidExpectationDefinition,
    SolidExpectationResult,
)

from .errors import (
    SolidUserCodeExecutionError, SolidTypeError, SolidExecutionFailureReason,
    SolidExpectationFailedError, SolidInvariantViolation
)
from .graph import DagsterPipeline

Metric = namedtuple('Metric', 'context_dict metric_name value')


class DagsterExecutionContext:
    '''
    A context object flowed through the entire scope of single execution of a
    pipeline of solids. This is used by both framework and uesr code to log
    messages and metrics. It also maintains a stack of context values so that
    logs, metrics, and any future reporting are reported with a minimal, consitent 
    level of context so that developers do not have to repeatedly log well-known
    information (e.g. the name of the solid, the name of the pipeline, etc) when
    logging. Additionally tool author may add their own context values to assist
    reporting.
    '''

    def __init__(self, loggers=None, log_level=ERROR):
        self._logger = CompositeLogger(loggers=loggers, level=log_level)
        self._context_dict = OrderedDict()
        self._metrics = []

    def _maybe_quote(self, val):
        str_val = str(val)
        if ' ' in str_val:
            return '"{val}"'.format(val=str_val)
        return str_val

    def _kv_message(self):
        return ' '.join(
            [
                '{key}={value}'.format(key=key, value=self._maybe_quote(value))
                for key, value in self._context_dict.items()
            ]
        )

    def _log(self, method, msg, frmtargs):
        check.str_param(method, 'method')
        check.str_param(msg, 'msg')
        check.dict_param(frmtargs, 'frmtargs')

        full_message = 'message="{message}" {kv_message}'.format(
            message=msg.format(**frmtargs), kv_message=self._kv_message()
        )
        getattr(self._logger, method)(full_message, extra=self._context_dict)

    def debug(self, msg, **frmtargs):
        return self._log('debug', msg, frmtargs)

    def info(self, msg, **frmtargs):
        return self._log('info', msg, frmtargs)

    def warn(self, msg, **frmtargs):
        return self._log('warn', msg, frmtargs)

    def error(self, msg, **frmtargs):
        return self._log('error', msg, frmtargs)

    def critical(self, msg, **frmtargs):
        return self._log('critical', msg, frmtargs)

    def exception(self, e):
        check.inst_param(e, 'e', Exception)

        # this is pretty lame right. should embellish with more data (stack trace?)
        return self._log('exception', str(e), {})

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


class DagsterExecutionResult:
    '''
    A class to represnet the result of the execution of a single solid. Pipeline
    commands return iterators or lists of these results.

    (TODO: explain the various error states)
    '''

    def __init__(
        self,
        success,
        solid,
        materialized_output,
        reason=None,
        exception=None,
        failed_expectation_results=None
    ):
        self.success = check.bool_param(success, 'success')
        if not success:
            check.param_invariant(
                isinstance(reason, SolidExecutionFailureReason), 'reason',
                'Must provide a reason is result is a failure'
            )
        self.materialized_output = materialized_output
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.reason = reason
        self.exception = check.opt_inst_param(exception, 'exception', Exception)

        if reason == SolidExecutionFailureReason.USER_CODE_ERROR:
            check.inst(exception, SolidUserCodeExecutionError)
            self.user_exception = exception.user_exception
        else:
            self.user_exception = None

        if reason == SolidExecutionFailureReason.EXPECTATION_FAILURE:
            check.invariant(
                failed_expectation_results is not None and failed_expectation_results != [],
                'Must have at least one expectation failure'
            )
            self.failed_expectation_results = check.list_param(
                failed_expectation_results,
                'failed_expectation_results',
                of_type=SolidExpectationResult
            )
        else:
            check.invariant(failed_expectation_results is None)
            self.failed_expectation_results = None

    def reraise_user_error(self):
        check.invariant(self.reason == SolidExecutionFailureReason.USER_CODE_ERROR)
        check.inst(self.exception, SolidUserCodeExecutionError)
        six.reraise(*self.exception.original_exc_info)

    @property
    def name(self):
        return self.solid.name

    def copy(self):
        ''' This must be used instead of copy.deepcopy() because exceptions cannot
        be deepcopied'''
        return DagsterExecutionResult(
            success=self.success,
            solid=self.solid,
            materialized_output=copy.deepcopy(self.materialized_output),
            reason=self.reason,
            exception=self.exception,
            failed_expectation_results=None if self.failed_expectation_results is None else
            [result.copy() for result in self.failed_expectation_results],
        )


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
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.str_param(msg, 'msg')

    try:
        yield
    except Exception as e:
        context.exception(e)
        raise SolidUserCodeExecutionError(
            msg.format(**kwargs), e, user_exception=e, original_exc_info=sys.exc_info()
        )


def _execute_input(context, input_definition, arg_dict):
    '''
    Check to ensure that the arguments to a particular input are valid, and then
    execute the input functinos. Wraps that execution in appropriate logging, metrics tracking,
    and a user-code error boundary.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(input_definition, 'input_defintion', SolidInputDefinition)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)

    with context.value('input', input_definition.name), context.value('arg_dict', arg_dict):
        expected_args = set(input_definition.argument_def_dict.keys())
        received_args = set(arg_dict.keys())
        if expected_args != received_args:
            raise SolidTypeError(
                'Argument mismatch in input {input_name}. Expected {expected} got {received}'.
                format(
                    input_name=input_definition.name,
                    expected=repr(expected_args),
                    received=repr(received_args),
                )
            )

        for arg_name, arg_value in arg_dict.items():
            arg_def_type = input_definition.argument_def_dict[arg_name]
            if not arg_def_type.is_python_valid_value(arg_value):
                format_string = (
                    'Expected type {typename} for arg {arg_name}' +
                    'for {input_name} but got {arg_value}'
                )
                raise SolidTypeError(
                    format_string.format(
                        typename=arg_def_type.name,
                        arg_name=arg_name,
                        input_name=input_definition.name,
                        arg_value=repr(arg_value),
                    )
                )

        error_str = 'Error occured while loading input "{input_name}"'
        with _user_code_error_boundary(context, error_str, input_name=input_definition.name):
            context.info('Entering input implementation')

            with time_execution_scope() as timer_result:
                materialized_input = input_definition.input_fn(context=context, arg_dict=arg_dict)

            context.metric('input_load_time_ms', timer_result.millis)

            return materialized_input


def _execute_input_expectation(context, expectation_def, materialized_input):
    '''
    Execute one user-specified input expectation on an input that has been instantiated in memory
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', SolidExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in input'
    with _user_code_error_boundary(context, error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_input)

    if not isinstance(expectation_result, SolidExpectationResult):
        raise SolidInvariantViolation(
            'Must return SolidExpectationResult from expectation function'
        )

    return expectation_result


def _execute_output_expectation(context, expectation_def, materialized_output):
    '''
    Execute one user-specified output expectation on an instantiated result of the core transform.
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', SolidExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in output'
    with _user_code_error_boundary(context, error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_output)

    if not isinstance(expectation_result, SolidExpectationResult):

        raise SolidInvariantViolation(
            'Must return SolidExpectationResult from expectation function'
        )

    return expectation_result


def _execute_core_transform(context, solid_transform_fn, materialized_inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    error_str = 'Error occured during core transform'
    with _user_code_error_boundary(context, error_str):
        with time_execution_scope() as timer_result:
            materialized_output = solid_transform_fn(context=context, **materialized_inputs)

        context.metric('core_transform_time_ms', timer_result.millis)

        check.invariant(
            not isinstance(materialized_output, DagsterExecutionResult),
            'Tricksy hobbitess cannot return an execution result from the transform ' + \
            'function in order to fool the framework'
        )

        return materialized_output


def _execute_output(context, output_def, output_arg_dict, materialized_output):
    '''
    Execute a single output, calling into user-specified code. Check validity
    of arguments into the output, do appropriate loggina and metrics tracking, and
    actually execute the output function with an appropriate error boundary. 
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(output_def, 'output_def', SolidOutputDefinition)
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)

    expected_args = set(output_def.argument_def_dict.keys())
    received_args = set(output_arg_dict.keys())

    if expected_args != received_args:
        raise SolidTypeError(
            'Argument mismatch in output. Expected {expected} got {received}'.format(
                expected=repr(expected_args),
                received=repr(received_args),
            )
        )

    for arg_name, arg_value in output_arg_dict.items():
        arg_def_type = output_def.argument_def_dict[arg_name]
        if not arg_def_type.is_python_valid_value(arg_value):
            raise SolidTypeError(
                'Expected type {typename} for arg {arg_name} in output but got {arg_value}'.format(
                    typename=arg_def_type.name,
                    arg_name=arg_name,
                    arg_value=repr(arg_value),
                )
            )

    error_str = 'Error during execution of output'
    with _user_code_error_boundary(context, error_str):
        context.info('Entering output implementation')
        output_def.output_fn(materialized_output, context=context, arg_dict=output_arg_dict)


SolidInputExpectationResult = namedtuple('SolidInputExpectionResult', 'input_name passes fails')


class SolidAllInputExpectationsRunResults:
    def __init__(self, run_results_list):
        self.run_results_list = check.list_param(
            run_results_list, 'run_results_list', of_type=SolidInputExpectationResult
        )

        all_passes = []
        all_fails = []
        for run_results in run_results_list:
            all_passes.extend(run_results.passes)
            all_fails.extend(run_results.fails)

        self.all_passes = all_passes
        self.all_fails = all_fails

    @property
    def success(self):
        return not self.all_fails


def _execute_all_input_expectations(context, solid, materialized_inputs):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    run_results_list = []

    for input_name in materialized_inputs.keys():
        input_def = solid.input_def_named(input_name)
        materialized_input = materialized_inputs[input_name]

        passes = []
        fails = []

        for input_expectation_def in input_def.expectations:
            input_expectation_result = _execute_input_expectation(
                context, input_expectation_def, materialized_input
            )

            if input_expectation_result.success:
                passes.append(input_expectation_result)
            else:
                fails.append(input_expectation_result)

        run_results_list.append(
            SolidInputExpectationResult(input_name=input_name, passes=passes, fails=fails)
        )

    return SolidAllInputExpectationsRunResults(run_results_list)


def _materialize_all_inputs(context, solid, input_arg_dicts):
    check.inst_param(context, 'context', DagsterExecutionContext)

    materialized_inputs = {}

    for input_name, arg_dict in input_arg_dicts.items():
        input_def = solid.input_def_named(input_name)
        materialized_input = _execute_input(context, input_def, arg_dict)
        materialized_inputs[input_name] = materialized_input

    return materialized_inputs


def _pipeline_solid(context, solid, input_arg_dicts):
    '''
    Execute the entire pipeline for a *single* solid, including input evaluation.
    '''

    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)

    materialized_inputs = _materialize_all_inputs(context, solid, input_arg_dicts)
    return _pipeline_solid_in_memory(context, solid, materialized_inputs)


def _pipeline_solid_in_memory(context, solid, materialized_inputs):
    '''
    Given inputs that are already materialized in memory. Evaluation all inputs expectations,
    execute the core transform, and then evaluate all output expectations.

    This is the core of the solid execution that does not touch any extenralized state, whether
    it be inputs or outputs.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    all_run_result = _execute_all_input_expectations(context, solid, materialized_inputs)

    if not all_run_result.success:
        return DagsterExecutionResult(
            success=False,
            materialized_output=None,
            solid=solid,
            reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=all_run_result.all_fails,
        )

    context.info('Executing core transform')

    materialized_output = _execute_core_transform(context, solid.transform_fn, materialized_inputs)

    if isinstance(materialized_output, DagsterExecutionResult):
        check.invariant(
            not materialized_output.success,
            'only failed things should return an execution result right here'
        )
        return materialized_output

    output_expectation_failures = []
    for output_expectation_def in solid.output_expectations:
        output_expectation_result = _execute_output_expectation(
            context, output_expectation_def, materialized_output
        )
        if not output_expectation_result.success:
            output_expectation_failures.append(output_expectation_result)

    if output_expectation_failures:
        return DagsterExecutionResult(
            success=False,
            materialized_output=None,
            solid=solid,
            reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=output_expectation_failures,
        )

    return materialized_output


def execute_single_solid(context, solid, input_arg_dicts, throw_on_error=True):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)

    results = list(
        execute_pipeline_iterator(context, DagsterPipeline(solids=[solid]), input_arg_dicts)
    )

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    if throw_on_error:
        _do_throw_on_error(execution_result)

    return execution_result


def _do_throw_on_error(execution_result):
    check.inst_param(execution_result, 'execution_result', DagsterExecutionResult)
    if not execution_result.success:
        if execution_result.reason == SolidExecutionFailureReason.EXPECTATION_FAILURE:
            check.invariant(
                execution_result.failed_expectation_results is not None
                and execution_result.failed_expectation_results != []
            )
            raise SolidExpectationFailedError(
                failed_expectation_results=execution_result.failed_expectation_results
            )
        elif execution_result.reason == SolidExecutionFailureReason.USER_CODE_ERROR:
            execution_result.reraise_user_error()

        check.invariant(execution_result.exception)
        raise execution_result.exception


def output_single_solid(
    context, solid, input_arg_dicts, output_type, output_arg_dict, throw_on_error=True
):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(output_type, 'output_type')
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = list(
        output_pipeline_iterator(
            context,
            DagsterPipeline(solids=[solid]),
            input_arg_dicts,
            output_arg_dicts={solid.name: {
                output_type: output_arg_dict
            }},
        )
    )

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    if throw_on_error:
        _do_throw_on_error(execution_result)

    return execution_result


def _select_keys(ddict1, ddict2, keys):
    ddict = {**ddict1, **ddict2}
    return {key: ddict[key] for key in keys}


def execute_pipeline_through_solid(context, pipeline, input_arg_dicts, solid_name):
    '''
    Execute a pipeline through a single solid, and then output *only* that result
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(solid_name, 'solid_name')

    for result in execute_pipeline_iterator(context, pipeline, input_arg_dicts, [solid_name]):
        if result.name == solid_name:
            return result

    check.failed('Result ' + solid_name + ' not found!')


def _execute_pipeline_solid_step(context, solid, input_arg_dicts, materialized_values):
    # The value produce by an inputs is potentially different per solid.
    # This is allowed so that two solids that do different materialization of the
    # same exact input (e.g. the same file) don't have to create additional solids
    # to account for this.

    input_values = {}

    context.info('About to materialize and gather all inputs')

    for inp in solid.inputs:
        if inp.name not in materialized_values and inp.name not in input_values:
            materialized = _execute_input(context, inp, input_arg_dicts[inp.name])
            input_values[inp.name] = materialized

    selected_values = _select_keys(input_values, materialized_values, solid.input_names)

    # This call does all input and output expectations, as well as the core transform
    materialized_output = _pipeline_solid_in_memory(context, solid, selected_values)

    if isinstance(materialized_output, DagsterExecutionResult):
        check.invariant(not materialized_output.success, 'early return should only be failure')
        return materialized_output

    check.invariant(solid.name not in materialized_values, 'should be not in materialized values')

    materialized_values[solid.name] = materialized_output

    return DagsterExecutionResult(
        success=True,
        solid=solid,
        materialized_output=materialized_values[solid.name],
        exception=None
    )


def execute_pipeline_iterator(context, pipeline, input_arg_dicts, through_solids=None):
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

    For formats of input_arg_dicts and output_arg_dicts see docblock at the top of the module
    '''

    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)

    input_names = list(input_arg_dicts.keys())
    output_names = pipeline.solid_names if not through_solids else through_solids

    for output_name in output_names:
        unprovided_inputs = pipeline.solid_graph.compute_unprovided_inputs(
            input_names=input_names, output_name=output_name
        )
        if unprovided_inputs:
            check.failed(
                'Failed to provide inputs {unprovided_inputs} for solid {name}'.format(
                    unprovided_inputs=unprovided_inputs, name=output_name
                )
            )

    # Given the inputs and outputs specific, create the subgraph of the pipeline
    # necessary to complete the computation
    execution_graph = pipeline.solid_graph.create_execution_graph(output_names, input_names)

    materialized_values = {}

    for solid in execution_graph.topological_solids:

        try:
            with context.value('solid', solid.name):
                execution_result = _execute_pipeline_solid_step(
                    context, solid, input_arg_dicts, materialized_values
                )

            yield execution_result

            if not execution_result.success:
                break

        except SolidUserCodeExecutionError as see:
            yield DagsterExecutionResult(
                success=False,
                reason=SolidExecutionFailureReason.USER_CODE_ERROR,
                solid=solid,
                materialized_output=None,
                exception=see,
            )
            break


def execute_pipeline(context, pipeline, input_arg_dicts, through_solids=None, throw_on_error=False):
    '''
    "Synchronous" version of execute_pipeline_iteator.

    throw_on_error makes the function throw when an error is encoutered rather than returning
    the SolidExecutionResult in an error-state.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions
    '''
    results = []
    for result in execute_pipeline_iterator(context, pipeline, input_arg_dicts, through_solids):
        if throw_on_error:
            if not result.success:
                _do_throw_on_error(result)

        results.append(result.copy())
    return results


def _check_output_arg_dicts(output_arg_dicts):
    check.dict_param(output_arg_dicts, 'output_arg_dicts', key_type=str, value_type=dict)
    for output_arg_dict in output_arg_dicts.values():
        check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str, value_type=dict)


def output_pipeline(context, pipeline, input_arg_dicts, output_arg_dicts, throw_on_error=False):
    '''
    Synchronous version of output_pipeline_iteator. Just like execute_pipeline, you can optionally
    specify, through thorw_on_error, that exceptions should be thrown when encountered instead
    of returning a result in an error state. Especially useful in testing contexts.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    _check_output_arg_dicts(output_arg_dicts)

    results = []
    for result in output_pipeline_iterator(context, pipeline, input_arg_dicts, output_arg_dicts):
        if throw_on_error:
            if not result.success:
                _do_throw_on_error(result)
        results.append(result.copy())
    return results


def output_pipeline_iterator(context, pipeline, input_arg_dicts, output_arg_dicts):
    '''
    Similar to execute_pipeline_iterator, except that you can specify outputs (per format
    specified in module docblock) to create externally accessible materializations of
    the computations in pipeline.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    _check_output_arg_dicts(output_arg_dicts)

    for result in execute_pipeline_iterator(
        context, pipeline, input_arg_dicts, through_solids=list(output_arg_dicts.keys())
    ):
        if not result.success:
            yield result
            break

        if result.name not in output_arg_dicts:
            yield result
            continue

        output_result = result

        for output_type, output_arg_dict in output_arg_dicts[result.name].items():
            output_def = result.solid.output_def_named(output_type)
            with context.value('solid', result.name), \
                context.value('output_type', output_def.name), \
                context.value('output_args', output_arg_dict):
                try:
                    _execute_output(
                        context, output_def, output_arg_dict, result.materialized_output
                    )
                except SolidUserCodeExecutionError as see:
                    output_result = DagsterExecutionResult(
                        success=False,
                        solid=result.solid,
                        reason=SolidExecutionFailureReason.USER_CODE_ERROR,
                        exception=see,
                        materialized_output=result.materialized_output,
                    )
                    break

        yield output_result

        if not output_result.success:
            break
