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
from collections import (namedtuple, OrderedDict)
from contextlib import contextmanager
import copy
import sys

import six

from dagster import check
from dagster import config

from dagster.utils.logging import (CompositeLogger, ERROR, get_formatted_stack_trace)
from dagster.utils.timing import time_execution_scope

from .definitions import (
    SolidDefinition, ExpectationDefinition, ExpectationResult, SourceDefinition,
    MaterializationDefinition
)

from .errors import (
    DagsterUserCodeExecutionError, DagsterTypeError, DagsterExecutionFailureReason,
    DagsterExpectationFailedError, DagsterInvariantViolationError
)
from .graph import DagsterPipeline

Metric = namedtuple('Metric', 'context_dict metric_name value')


class DagsterExecutionContext:
    '''
    A context object flowed through the entire scope of single execution of a
    pipeline of solids. This is used by both framework and uesr code to log
    messages and metrics. It also maintains a stack of context values so that
    logs, metrics, and any future reporting are reported with a minimal, consistent
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

    def _kv_message(self, extra=None):
        extra = check.opt_dict_param(extra, 'extra')
        return ' '.join(
            [
                '{key}={value}'.format(key=key, value=self._maybe_quote(value))
                for key, value in [*self._context_dict.items(), *extra.items()]
            ]
        )

    def _log(self, method, msg, **kwargs):
        check.str_param(method, 'method')
        check.str_param(msg, 'msg')

        full_message = 'message="{message}" {kv_message}'.format(
            message=msg, kv_message=self._kv_message(kwargs)
        )

        log_props = copy.copy(self._context_dict)
        log_props['log_message'] = msg

        getattr(self._logger, method)(full_message, extra={**log_props, **kwargs})

    def debug(self, msg, **kwargs):
        return self._log('debug', msg, **kwargs)

    def info(self, msg, **kwargs):
        return self._log('info', msg, **kwargs)

    def warn(self, msg, **kwargs):
        return self._log('warn', msg, **kwargs)

    def error(self, msg, **kwargs):
        return self._log('error', msg, **kwargs)

    def critical(self, msg, **kwargs):
        return self._log('critical', msg, **kwargs)

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
        result_list,
    ):
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=DagsterExecutionResult
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


class DagsterExecutionResult:
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
        failed_expectation_results=None,
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

        if reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
            check.inst(exception, DagsterUserCodeExecutionError)
            self.user_exception = exception.user_exception
        else:
            self.user_exception = None

        if reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE:
            check.invariant(
                failed_expectation_results is not None and failed_expectation_results != [],
                'Must have at least one expectation failure'
            )
            self.failed_expectation_results = check.list_param(
                failed_expectation_results, 'failed_expectation_results', of_type=ExpectationResult
            )
        else:
            check.invariant(failed_expectation_results is None)
            self.failed_expectation_results = None

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
        return DagsterExecutionResult(
            success=self.success,
            solid=self.solid,
            transformed_value=copy.deepcopy(self.transformed_value),
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
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(source_definition, 'source_definition', SourceDefinition)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)

    with context.value('source_type', source_definition.source_type), \
         context.value('arg_dict', arg_dict):
        expected_args = set(source_definition.argument_def_dict.keys())
        received_args = set(arg_dict.keys())
        if expected_args != received_args:
            raise DagsterTypeError(
                'Argument mismatch in source type {source}. Expected {expected} got {received}'.
                format(
                    source=source_definition.source_type,
                    expected=repr(expected_args),
                    received=repr(received_args),
                )
            )

        for arg_name, arg_value in arg_dict.items():
            arg_def_type = source_definition.argument_def_dict[arg_name]
            if not arg_def_type.is_python_valid_value(arg_value):
                format_string = (
                    'Expected type {typename} for arg {arg_name}' +
                    'for {source_type} but got {arg_value}'
                )
                raise DagsterTypeError(
                    format_string.format(
                        typename=arg_def_type.name,
                        arg_name=arg_name,
                        source_type=source_definition.source_type,
                        arg_value=repr(arg_value),
                    )
                )

        error_str = 'Error occured while loading source "{source_type}"'
        with _user_code_error_boundary(
            context,
            error_str,
            source_type=source_definition.source_type,
        ):
            context.info('Entering input implementation')

            with time_execution_scope() as timer_result:
                value = source_definition.source_fn(context, arg_dict)

            context.metric('input_load_time_ms', timer_result.millis)

            return value


def _execute_input_expectation(context, expectation_def, value):
    '''
    Execute one user-specified input expectation on an input that has been instantiated in memory
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in input'
    with _user_code_error_boundary(context, error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(value)

    if not isinstance(expectation_result, ExpectationResult):
        raise DagsterInvariantViolationError(
            'Must return SolidExpectationResult from expectation function'
        )

    return expectation_result


def _execute_output_expectation(context, expectation_def, transformed_value):
    '''
    Execute one user-specified output expectation on an instantiated result of the core transform.
    Wraps computation in an error boundary and performs all necessary logging and metrics tracking
    (TODO: actually log and track metrics!)
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in output'
    with _user_code_error_boundary(context, error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(transformed_value)

    if not isinstance(expectation_result, ExpectationResult):

        raise DagsterInvariantViolationError(
            'Must return SolidExpectationResult from expectation function'
        )

    return expectation_result


def _execute_core_transform(context, solid_transform_fn, values_dict):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(values_dict, 'values_dict', key_type=str)

    error_str = 'Error occured during core transform'
    with _user_code_error_boundary(context, error_str):
        with time_execution_scope() as timer_result:
            transformed_value = solid_transform_fn(context, values_dict)

        context.metric('core_transform_time_ms', timer_result.millis)

        check.invariant(
            not isinstance(transformed_value, DagsterExecutionResult),
            'Tricksy hobbitess cannot return an execution result from the transform ' + \
            'function in order to fool the framework'
        )

        return transformed_value


def _execute_materialization(context, materialiation_def, arg_dict, value):
    '''
    Execute a single output, calling into user-specified code. Check validity
    of arguments into the output, do appropriate loggina and metrics tracking, and
    actually execute the output function with an appropriate error boundary.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
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
        if not arg_def_type.is_python_valid_value(arg_value):
            raise DagsterTypeError(
                'Expected type {typename} for arg {arg_name} in output but got {arg_value}'.format(
                    typename=arg_def_type.name,
                    arg_name=arg_name,
                    arg_value=repr(arg_value),
                )
            )

    error_str = 'Error during execution of materialization'
    with _user_code_error_boundary(context, error_str):
        context.info('Entering materialization implementation')
        materialiation_def.materialization_fn(context, arg_dict, value)


InputExpectationResult = namedtuple('InputExpectionResult', 'input_name passes fails')


class AllInputExpectationsRunResults:
    def __init__(self, run_results_list):
        self.run_results_list = check.list_param(
            run_results_list, 'run_results_list', of_type=InputExpectationResult
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


def _execute_all_input_expectations(context, solid, values_dict):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.dict_param(values_dict, 'values_dict', key_type=str)

    run_results_list = []

    for input_name in values_dict.keys():
        input_def = solid.input_def_named(input_name)
        value = values_dict[input_name]

        passes = []
        fails = []

        for input_expectation_def in input_def.expectations:
            input_expectation_result = _execute_input_expectation(
                context, input_expectation_def, value
            )

            if input_expectation_result.success:
                passes.append(input_expectation_result)
            else:
                fails.append(input_expectation_result)

        run_results_list.append(
            InputExpectationResult(input_name=input_name, passes=passes, fails=fails)
        )

    return AllInputExpectationsRunResults(run_results_list)


def _pipeline_solid_in_memory(context, solid, transform_values_dict):
    '''
    Given inputs that are already in memory. Evaluation all inputs expectations,
    execute the core transform, and then evaluate all output expectations.

    This is the core of the solid execution that does not touch any extenralized state, whether
    it be inputs or outputs.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.dict_param(transform_values_dict, 'transform_values_dict', key_type=str)

    all_run_result = _execute_all_input_expectations(context, solid, transform_values_dict)

    if not all_run_result.success:
        return DagsterExecutionResult(
            success=False,
            transformed_value=None,
            solid=solid,
            reason=DagsterExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=all_run_result.all_fails,
        )

    context.info('Executing core transform')

    transformed_value = _execute_core_transform(context, solid.transform_fn, transform_values_dict)

    if isinstance(transformed_value, DagsterExecutionResult):
        check.invariant(
            not transformed_value.success,
            'only failed things should return an execution result right here'
        )
        return transformed_value

    if solid.output.output_callback:
        solid.output.output_callback(context, transformed_value)

    output_expectation_failures = []
    for output_expectation_def in solid.output.expectations:
        output_expectation_result = _execute_output_expectation(
            context, output_expectation_def, transformed_value
        )
        if not output_expectation_result.success:
            output_expectation_failures.append(output_expectation_result)

    if output_expectation_failures:
        return DagsterExecutionResult(
            success=False,
            transformed_value=None,
            solid=solid,
            reason=DagsterExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=output_expectation_failures,
        )

    return transformed_value


def execute_single_solid(context, solid, environment, throw_on_error=True):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = list(
        execute_pipeline_iterator(
            context, DagsterPipeline(solids=[solid]), environment=environment
        )
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
        if execution_result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE:
            check.invariant(
                execution_result.failed_expectation_results is not None
                and execution_result.failed_expectation_results != []
            )
            raise DagsterExpectationFailedError(
                failed_expectation_results=execution_result.failed_expectation_results
            )
        elif execution_result.reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
            execution_result.reraise_user_error()

        check.invariant(execution_result.exception)
        raise execution_result.exception


def create_single_solid_env_from_arg_dicts(solid, arg_dicts):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.dict_param(arg_dicts, 'arg_dicts', key_type=str, value_type=dict)

    input_sources = {}
    input_to_source_type = {}
    for input_def in solid.inputs:
        check.invariant(len(input_def.sources) == 1)
        input_to_source_type[input_def.name] = input_def.sources[0].source_type

    input_sources = []

    for input_name, arg_dict in arg_dicts.items():
        input_sources.append(
            config.Input(
                input_name=input_name,
                source=input_to_source_type[input_name],
                args=arg_dict,
            )
        )

    return config.Environment(input_sources=input_sources)


# This is the legacy format for specifying inputs.

# Keeping this around because the clarify pipeline is still using this as we finalize
# the real config inputs. We don't want to thrash that pipeline until we finalize
# the input api

# input_arg_dicts: {string : { string: string } }

# A dictionary of dictionaries. The first level is indexed by input *name*. Put an entry for each
# input you want to specify. Each one of inputs in turn has an argument dictionary, which is just
# a set of key value pairs, represented by a bare python dictionary:

# So for example a solid that takes two csv inputs would have the input_arg_dicts:

# {
#     "csv_one" : { "path" : "path/to/csv_one.csv},
#     "csv_two" : { "path" : "path/to/csv_two.csv},
# }


def create_pipeline_env_from_arg_dicts(pipeline, arg_dicts):
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.dict_param(arg_dicts, 'arg_dicts', key_type=str, value_type=dict)

    input_sources = {}
    input_to_source_type = {}

    for solid in pipeline.solids:
        for input_def in solid.inputs:
            if input_def.sources:
                input_to_source_type[input_def.name] = input_def.sources[0].source_type

    input_sources = []
    for input_name, arg_dict in arg_dicts.items():
        if input_name in input_to_source_type:
            input_sources.append(
                config.Input(
                    input_name=input_name,
                    source=input_to_source_type[input_name],
                    args=arg_dict,
                )
            )

    return config.Environment(input_sources=input_sources)


def _convert_environment_dict_to_environment_namedtuple(environment_dict):
    check.dict_param(environment_dict, 'environment_dict')

    def _to_input_source(input_source_dict):
        for input_name, source_dict in input_source_dict.items():
            yield config.Input(input_name, source_dict['source_type'], source_dict['args'])

    return config.Environment(
        input_sources=list(_to_input_source(environment_dict['input_sources'])),
    )


def output_single_solid(
    context,
    solid,
    environment,
    materialization_type,
    arg_dict,
    throw_on_error=True,
):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.str_param(materialization_type, 'materialization_type')
    check.dict_param(arg_dict, 'arg_dict', key_type=str)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = list(
        materialize_pipeline_iterator(
            context,
            DagsterPipeline(solids=[solid]),
            environment=environment,
            materializations=[
                config.Materialization(
                    solid=solid.name, materialization_type=materialization_type, args=arg_dict
                )
            ],
        )
    )

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    if throw_on_error:
        _do_throw_on_error(execution_result)

    return execution_result


def execute_pipeline_through_solid(
    context,
    pipeline,
    *,
    environment,
    solid_name,
):
    '''
    Execute a pipeline through a single solid, and then output *only* that result
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.inst_param(environment, 'environment', config.Environment)
    check.str_param(solid_name, 'solid_name')

    for result in execute_pipeline_iterator(
        context, pipeline, environment=environment, through_solids=[solid_name]
    ):

        if result.name == solid_name:
            return result

    check.failed('Result ' + solid_name + ' not found!')


def _gather_input_values(context, solid, input_args, intermediate_values):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_args, 'input_args', InputArgs)
    check.dict_param(intermediate_values, 'intermediate_values')

    context.info('About to instantiate and gather all inputs')

    input_values = {}
    for input_def in solid.inputs:
        with context.value('input', input_def.name):
            if input_def.depends_on and input_def.depends_on.name in intermediate_values:
                # grab value from dependency
                input_values[input_def.name] = intermediate_values[input_def.depends_on.name]
            else:
                # must get value from source
                source_def = input_args.source_for_input(solid.name, input_def.name)
                new_value = _read_source(
                    context, source_def, input_args.args_for_input(input_def.name)
                )
                input_values[input_def.name] = new_value

            if input_def.input_callback:
                input_def.input_callback(context, input_values[input_def.name])
    return input_values


def _execute_pipeline_solid_step(context, solid, input_args, intermediate_values):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_args, 'input_args', InputArgs)
    check.dict_param(intermediate_values, 'intermediate_values')

    # The value produce by an inputs is potentially different per solid.
    # This is allowed so that two solids that do different instantiation of the
    # same exact input (e.g. the same file) don't have to create additional solids
    # to account for this.

    input_values = _gather_input_values(context, solid, input_args, intermediate_values)

    # This call does all input and output expectations, as well as the core transform
    transformed_value = _pipeline_solid_in_memory(context, solid, input_values)

    if isinstance(transformed_value, DagsterExecutionResult):
        check.invariant(not transformed_value.success, 'early return should only be failure')
        return transformed_value

    check.invariant(solid.name not in intermediate_values, 'should be not in intermediate values')

    context.debug(
        'About to set {output} for {name}'.format(
            output=repr(transformed_value),
            name=solid.name,
        )
    )

    intermediate_values[solid.name] = transformed_value

    return DagsterExecutionResult(
        success=True,
        solid=solid,
        transformed_value=intermediate_values[solid.name],
        exception=None
    )


class InputArgs:
    def __init__(self, pipeline, environment):
        self.pipeline = check.inst_param(pipeline, 'pipeline', DagsterPipeline)
        self.environment = check.inst_param(environment, 'environment', config.Environment)

    @property
    def input_names(self):
        return [input_source.input_name for input_source in self.environment.input_sources]

    def source_for_input(self, solid_name, input_name):
        input_source = self.environment.input_named(input_name)

        input_def = self.pipeline.get_input(solid_name, input_name)

        if not input_source.source:
            check.invariant(len(input_def.sources) == 1)
            return input_def.sources[0]

        return input_def.source_of_type(input_source.source)

    def args_for_input(self, input_name):
        return self.environment.input_named(input_name).args


def execute_pipeline_iterator(
    context,
    pipeline,
    environment,
    through_solids=None,
    from_solids=None,
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

    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.inst_param(environment, 'environment', config.Environment)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)
    check.opt_list_param(from_solids, 'from_solids', of_type=str)

    pipeline_context_value = pipeline.name if pipeline.name else 'unnamed'

    with context.value('pipeline', pipeline_context_value):
        input_args = InputArgs(pipeline, environment)

        provided_input_names = input_args.input_names

        if not through_solids:
            through_solids = pipeline.all_sink_solids

        if not from_solids:
            all_deps = set()
            for through_solid in through_solids:
                all_deps.union(pipeline.solid_graph.transitive_dependencies_of(through_solid))

            from_solids = list(all_deps)

        for input_name in provided_input_names:
            if not pipeline.has_input(input_name):
                raise DagsterInvariantViolationError(
                    f'Input "{input_name}" not found in the pipeline.' + \
                    f'Input must be one of {repr(pipeline.input_names)}'
                )

        for through_solid_name in through_solids:
            unprovided_inputs = pipeline.solid_graph.compute_unprovided_inputs(
                input_names=provided_input_names, solid_name=through_solid_name
            )
            if unprovided_inputs:
                check.failed(
                    'Failed to provide inputs {unprovided_inputs} for solid {name}'.format(
                        unprovided_inputs=unprovided_inputs, name=through_solid_name
                    )
                )

        execution_graph = pipeline.solid_graph.create_execution_subgraph(
            from_solids, list(through_solids)
        )

        intermediate_values = {}

        for solid in execution_graph.topological_solids:

            try:
                with context.value('solid', solid.name):
                    execution_result = _execute_pipeline_solid_step(
                        context, solid, input_args, intermediate_values
                    )

                yield execution_result

                if not execution_result.success:
                    break

            except DagsterUserCodeExecutionError as see:
                yield DagsterExecutionResult(
                    success=False,
                    reason=DagsterExecutionFailureReason.USER_CODE_ERROR,
                    solid=solid,
                    transformed_value=None,
                    exception=see,
                )
                break


def execute_pipeline(
    context,
    pipeline,
    *,
    environment,
    from_solids=None,
    through_solids=None,
    throw_on_error=True,
):
    '''
    "Synchronous" version of execute_pipeline_iteator.

    throw_on_error makes the function throw when an error is encoutered rather than returning
    the SolidExecutionResult in an error-state.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.inst_param(environment, 'environment', config.Environment)
    from_solids = check.opt_list_param(from_solids, 'from_solids', of_type=str)
    through_solids = check.opt_list_param(through_solids, 'through_solids', of_type=str)
    check.bool_param(throw_on_error, 'throw_on_error')

    check.bool_param(throw_on_error, 'throw_on_error')

    results = []
    for result in execute_pipeline_iterator(
        context,
        pipeline,
        through_solids=through_solids,
        environment=environment,
        from_solids=from_solids,
    ):
        if throw_on_error:
            if not result.success:
                _do_throw_on_error(result)

        results.append(result.copy())
    return DagsterPipelineExecutionResult(results)


class MaterializationArgs:
    def __init__(self, pipeline, materializations):
        check.inst_param(pipeline, 'pipeline', DagsterPipeline)
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


def materialize_pipeline(
    context,
    pipeline,
    *,
    environment,
    materializations,
    throw_on_error=True,
):
    '''
    Synchronous version of materialize_pipeline_iterator. Just like execute_pipeline, you
    can optionally specify, through throw_on_error, that exceptions should be thrown when
    encountered instead of returning a result in an error state. Especially useful in testing
    contexts.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.inst_param(environment, 'environment', config.Environment)
    check.list_param(materializations, 'materializations', of_type=config.Materialization)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = []
    for result in materialize_pipeline_iterator(
        context,
        pipeline,
        materializations=materializations,
        environment=environment,
    ):
        if throw_on_error:
            if not result.success:
                _do_throw_on_error(result)
        results.append(result.copy())
    return DagsterPipelineExecutionResult(results)


def materialize_pipeline_iterator(
    context,
    pipeline,
    *,
    materializations,
    environment,
    through_solids=None,
    from_solids=None,
    use_materialization_through_solids=True,
):
    '''
    Similar to execute_pipeline_iterator, except that you can specify outputs (per format
    specified in module docblock) to create externally accessible materializations of
    the computations in pipeline.
    '''
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)
    check.list_param(materializations, 'materializations', of_type=config.Materialization)
    check.inst_param(environment, 'environment', config.Environment)

    materialization_args = MaterializationArgs(pipeline, materializations)

    if through_solids is None and use_materialization_through_solids:
        through_solids = materialization_args.through_solids

    for result in execute_pipeline_iterator(
        context,
        pipeline,
        through_solids=through_solids,
        from_solids=from_solids,
        environment=environment
    ):
        if not result.success:
            yield result
            break

        if not materialization_args.should_materialize(result.name):
            yield result
            continue

        materialization_result = result

        materializations = materialization_args.materializations_for_solid(result.name)

        solid = pipeline.solid_named(result.name)

        with context.value('solid', result.name):
            for materialization in materializations:
                arg_dict = materialization.args
                materialization_type = materialization.materialization_type
                with context.value('materialization_type', materialization_type), \
                    context.value('materialization_args', arg_dict):
                    try:
                        mat_def = solid.output.materialization_of_type(materialization_type)
                        _execute_materialization(
                            context, mat_def, arg_dict, result.transformed_value
                        )
                    except DagsterUserCodeExecutionError as see:
                        materialization_result = DagsterExecutionResult(
                            success=False,
                            solid=result.solid,
                            reason=DagsterExecutionFailureReason.USER_CODE_ERROR,
                            exception=see,
                            transformed_value=result.transformed_value,
                        )
                        break

        yield materialization_result

        if not materialization_result.success:
            break
