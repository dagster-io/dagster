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
    DagsterSelectorType,
    DagsterType,
    PythonObjectType,
    Any,
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


def throwing_evaluate_input_value(dagster_type, value):
    result = evaluate_input_value(dagster_type, value)
    if not result.success:
        stack = result.errors[0].stack
        raise DagsterEvaluateValueError(result.errors[0].message, stack=result.errors[0].stack)
    return result.value


def evaluate_input_value(dagster_type, value):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    collector = ErrorCollector()
    value = _evaluate_input_value(dagster_type, value, EvaluationStack(entries=[]), collector)
    if collector.errors:
        return EvaluateValueResult(success=False, value=None, errors=collector.errors)
    else:
        return EvaluateValueResult(success=True, value=value, errors=[])


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


def permissive_idx(ddict, key):
    check.opt_dict_param(ddict, 'ddict')
    check.str_param(key, 'key')
    if ddict is None:
        return None
    return ddict.get(key)


def evaluate_selector_input_value(dagster_type, incoming_value, collector, stack):
    check.inst_param(dagster_type, 'dagster_type', DagsterSelectorType)
    check.inst_param(collector, 'collector', ErrorCollector)
    check.inst_param(stack, 'stack', EvaluationStack)

    if incoming_value and not isinstance(incoming_value, dict):
        collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value for selector type {type_name} must be a dict got {value}'.format(
                    type_name=dagster_type.name,
                    value=incoming_value,
                ),
                error_data=RuntimeMismatchErrorData(
                    dagster_type=dagster_type,
                    value_rep=repr(incoming_value),
                ),
            )
        )
        return None

    if incoming_value and len(incoming_value) > 1:
        incoming_fields = sorted(list(incoming_value.keys()))
        defined_fields = sorted(list(dagster_type.field_dict.keys()))
        collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'You can only specify a single field. You specified {incoming_fields}. '
                    'The available fields are {defined_fields}'
                ).format(
                    incoming_fields=incoming_fields,
                    defined_fields=defined_fields,
                ),
                error_data=None
            )
        )
        return None

    if not incoming_value:
        if len(dagster_type.field_dict) > 1:
            collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                    message='Must specify a field if more than one defined',
                    error_data=None,
                )
            )
        field_name, field_def = single_item(dagster_type.field_dict)
        incoming_field_value = field_def.default_value if field_def.default_provided else None
    else:
        field_name, incoming_field_value = single_item(incoming_value)

    if field_name not in dagster_type.field_dict:
        collector.add_error(
            create_field_not_defined_error(
                dagster_type,
                stack,
                set(dagster_type.field_dict.keys()),
                field_name,
            )
        )
        return None

    parent_field = dagster_type.field_dict[field_name]
    field_value = _evaluate_input_value(
        parent_field.dagster_type,
        incoming_field_value,
        stack_with_field(stack, field_name, parent_field),
        collector,
    )
    return {field_name: field_value}


def _evaluate_input_value(dagster_type, value, stack, collector):
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
    elif isinstance(dagster_type, DagsterSelectorType):
        return evaluate_selector_input_value(dagster_type, value, collector, stack)
    elif isinstance(dagster_type, DagsterCompositeType):
        return evaluate_composite_input_value(dagster_type, value, collector, stack)
    elif isinstance(dagster_type, PythonObjectType):
        check.failed('PythonObjectType should not be used in a config hierarchy')
    elif dagster_type == Any:
        return value
    else:
        check.failed('Unknown type {name}'.format(name=dagster_type.name))


def evaluate_composite_input_value(dagster_composite_type, incoming_value, collector, stack):
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

    for received_field in incoming_fields:
        if received_field not in defined_fields:
            local_collector.add_error(
                create_field_not_defined_error(
                    dagster_composite_type,
                    stack,
                    defined_fields,
                    received_field,
                )
            )

    for expected_field, field_def in field_dict.items():
        if field_def.is_optional:
            continue

        check.invariant(not field_def.default_provided)

        if expected_field not in incoming_fields:
            local_collector.add_error(
                create_missing_required_field_error(
                    dagster_composite_type,
                    stack,
                    defined_fields,
                    expected_field,
                )
            )

    processed_fields = {}

    for expected_field, field_def in field_dict.items():
        if expected_field in incoming_fields:
            evaluated_value = _evaluate_input_value(
                field_def.dagster_type,
                incoming_value[expected_field],
                stack_with_field(stack, expected_field, field_def),
                collector,
            )
            processed_fields[expected_field] = evaluated_value
        elif field_def.default_provided:
            processed_fields[expected_field] = field_def.default_value
        elif not field_def.is_optional:
            check.invariant(
                bool(local_collector.errors),
                'Error should have been added for missing required field',
            )

    collector.errors = collector.errors + local_collector.errors

    return None if local_collector.errors else dagster_composite_type.construct_value(
        processed_fields
    )


def create_field_not_defined_error(dagster_composite_type, stack, defined_fields, received_field):
    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Field "{received}" is not defined on "{type_name}" Defined {defined}'.format(
            type_name=dagster_composite_type.name,
            defined=repr(defined_fields),
            received=received_field,
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_missing_required_field_error(dagster_type, stack, defined_fields, expected_field):
    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required field "{expected}" on "{type_name}". '
            'Defined fields: {defined}'
        ).format(
            expected=expected_field,
            type_name=dagster_type.name,
            defined=repr(defined_fields),
        ),
        error_data=MissingFieldErrorData(field_name=expected_field),
    )
