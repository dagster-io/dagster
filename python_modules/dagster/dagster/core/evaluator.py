from collections import namedtuple

from dagster import check

from .errors import (
    DagsterEvaluateValueError,
    DagsterEvaluationErrorReason,
    FieldNotDefinedErrorData,
    MissingFieldErrorData,
    RuntimeMismatchErrorData,
)

from .types import (
    DagsterCompositeType,
    DagsterScalarType,
    DagsterType,
    PythonObjectType,
)


class EvaluationStack(namedtuple('_EvaluationStack', 'entries')):
    def __new__(cls, entries):
        return super(EvaluationStack, cls).__new__(
            cls,
            check.list_param(entries, 'entries', of_type=EvaluationStackEntry),
        )

    @property
    def levels(self):
        return [entry.field_name for entry in self.entries]


EvaluationStackEntry = namedtuple('EvaluationStackEntry', 'field_name field_def')

EvaluationError = namedtuple('EvaluationError', 'stack reason message error_data')


class EvaluateValueResult(namedtuple('_EvaluateValueResult', 'success value errors')):
    def __new__(cls, success, value, errors):
        return super(EvaluateValueResult, cls).__new__(
            cls,
            check.bool_param(success, 'success'),
            value,
            check.list_param(errors, 'errors', of_type=EvaluationError),
        )

    def errors_at_level(self, *levels):
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(self, levels):
        check.list_param(levels, 'levels', of_type=str)
        for error in self.errors:
            if error.stack.levels == levels:
                yield error


class ErrorCollector:
    def __init__(self):
        self.errors = []

    def add_error(self, error):
        check.inst_param(error, 'error', EvaluationError)
        self.errors.append(error)


def stack_with_field(stack, field_name, field_def):
    return EvaluationStack(entries=stack.entries + [EvaluationStackEntry(field_name, field_def)])


def evaluate_value(dagster_type, value):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    collector = ErrorCollector()
    value = _evaluate_value(dagster_type, value, EvaluationStack(entries=[]), collector)
    if collector.errors:
        return EvaluateValueResult(success=False, value=None, errors=collector.errors)
    else:
        return EvaluateValueResult(success=True, value=value, errors=[])


def _evaluate_value(dagster_type, value, stack, collector):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    check.inst_param(stack, 'stack', EvaluationStack)
    check.inst_param(collector, 'collector', ErrorCollector)

    if isinstance(dagster_type, DagsterScalarType):
        if dagster_type.is_python_valid_value(value):
            return dagster_type.evaluate_value(value)
        else:
            collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                    message='Value {value} is not valid for type {type_name}'.format(
                        value=value,
                        type_name=dagster_type.name,
                    ),
                    error_data=RuntimeMismatchErrorData(
                        dagster_type=dagster_type,
                        value_rep=repr(value),
                    ),
                )
            )
            return None
    elif isinstance(dagster_type, DagsterCompositeType):
        return evaluate_composite_value(dagster_type, value, collector, stack)
    elif isinstance(dagster_type, PythonObjectType):
        check.failed('PythonObjectType should not be used in a config hierarchy')
    else:
        check.failed('Type not composite or scalar {name}'.format(name=dagster_type.name))


def evaluate_composite_value(dagster_composite_type, incoming_value, collector, stack):
    check.inst_param(dagster_composite_type, 'dagster_composite_type', DagsterCompositeType)
    check.inst_param(collector, 'collector', ErrorCollector)
    check.inst_param(stack, 'stack', EvaluationStack)

    local_collector = ErrorCollector()

    if incoming_value and not isinstance(incoming_value, dict):
        local_collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value for composite type {type_name} must be a dict got {value}'.format(
                    type_name=dagster_composite_type.name,
                    value=incoming_value,
                ),
                error_data=RuntimeMismatchErrorData(
                    dagster_type=dagster_composite_type,
                    value_rep=repr(incoming_value),
                ),
            )
        )
        collector.errors = collector.errors + local_collector.errors
        return None

    incoming_value = check.opt_dict_param(incoming_value, 'incoming_value', key_type=str)

    field_dict = dagster_composite_type.field_dict

    defined_fields = set(field_dict.keys())
    incoming_fields = set(incoming_value.keys())

    for received_arg in incoming_fields:
        if received_arg not in defined_fields:
            local_collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
                    message=(
                        'Field "{received}" is not defined on "{type_name}". '
                        'Defined {defined}'
                    ).format(
                        type_name=dagster_composite_type.name,
                        defined=repr(defined_fields),
                        received=received_arg,
                    ),
                    error_data=FieldNotDefinedErrorData(field_name=received_arg),
                ),
            )

    for expected_field, field_def in field_dict.items():
        if field_def.is_optional:
            continue

        check.invariant(not field_def.default_provided)

        if expected_field not in incoming_fields:
            local_collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
                    message=(
                        'Missing required field "{expected}" on "{type_name}". '
                        'Defined fields: {defined}'
                    ).format(
                        expected=expected_field,
                        type_name=dagster_composite_type.name,
                        defined=repr(defined_fields),
                    ),
                    error_data=MissingFieldErrorData(field_name=expected_field),
                ),
            )

    fields_to_pass = {}

    for expected_field, field_def in field_dict.items():
        if expected_field in incoming_fields:
            evaluated_value = _evaluate_value(
                field_def.dagster_type,
                incoming_value[expected_field],
                stack_with_field(stack, expected_field, field_def),
                collector,
            )
            fields_to_pass[expected_field] = evaluated_value
        elif field_def.default_provided:
            fields_to_pass[expected_field] = field_def.default_value
        else:
            check.invariant(
                bool(local_collector.errors),
                'Error should have been added for missing required field',
            )

    collector.errors = collector.errors + local_collector.errors

    return None if local_collector.errors else fields_to_pass
