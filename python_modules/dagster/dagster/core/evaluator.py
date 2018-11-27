from collections import namedtuple
from enum import Enum

from dagster import check

from .errors import DagsterError

from .types import (
    Any,
    DagsterCompositeType,
    DagsterScalarType,
    DagsterSelectorType,
    DagsterType,
    Field,
    PythonObjectType,
    _DagsterListType,
)


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class FieldNotDefinedErrorData(namedtuple('_FieldNotDefinedErrorData', 'field_name')):
    def __new__(cls, field_name):
        return super(FieldNotDefinedErrorData, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
        )


class MissingFieldErrorData(namedtuple('_MissingFieldErrorData', 'field_name field_def')):
    def __new__(cls, field_name, field_def):
        return super(MissingFieldErrorData, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check.inst_param(field_def, 'field_def', Field),
        )


class RuntimeMismatchErrorData(namedtuple('_RuntimeMismatchErrorData', 'dagster_type value_rep')):
    def __new__(cls, dagster_type, value_rep):
        return super(RuntimeMismatchErrorData, cls).__new__(
            cls,
            check.inst_param(dagster_type, 'dagster_type', DagsterType),
            check.str_param(value_rep, 'value_rep'),
        )


class SelectorTypeErrorData(namedtuple('_SelectorTypeErrorData', 'incoming_fields')):
    def __new__(cls, incoming_fields):
        return super(SelectorTypeErrorData, cls).__new__(
            cls,
            check.list_param(incoming_fields, 'incoming_fields', of_type=str),
        )


ERROR_DATA_TYPES = (
    FieldNotDefinedErrorData,
    MissingFieldErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
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


class EvaluationStackEntry:  # marker interface
    pass


class EvaluationStackPathEntry(
    namedtuple('_EvaluationStackEntry', 'field_name field_def'),
    EvaluationStackEntry,
):
    def __new__(cls, field_name, field_def):
        return super(EvaluationStackPathEntry, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check.inst_param(field_def, 'field_def', Field),
        )


class EvaluationStackListItemEntry(
    namedtuple('_EvaluationStackListItemEntry', 'list_index'),
    EvaluationStackEntry,
):
    def __new__(cls, list_index):
        check.opt_int_param(list_index, 'list_index')
        check.param_invariant(list_index is None or list_index >= 0, 'list_index')
        return super(EvaluationStackListItemEntry, cls).__new__(
            cls,
            list_index,
        )


class EvaluationError(namedtuple('_EvaluationError', 'stack reason message error_data')):
    def __new__(cls, stack, reason, message, error_data):
        return super(EvaluationError, cls).__new__(
            cls,
            check.inst_param(stack, 'stack', EvaluationStack),
            check.inst_param(reason, 'reason', DagsterEvaluationErrorReason),
            check.str_param(message, 'message'),
            check.inst_param(error_data, 'error_data', ERROR_DATA_TYPES),
        )


class DagsterEvaluateConfigValueError(DagsterError):
    '''Indicates invalid value was passed to a type's evaluate_value method'''

    def __init__(self, stack, *args, **kwargs):
        super(DagsterEvaluateConfigValueError, self).__init__(*args, **kwargs)
        self.stack = check.inst_param(stack, 'stack', EvaluationStack)


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
    return EvaluationStack(
        entries=stack.entries + [EvaluationStackPathEntry(field_name, field_def)]
    )


def stack_with_list_index(stack, list_index):
    return EvaluationStack(entries=stack.entries + [EvaluationStackListItemEntry(list_index)])


def throwing_evaluate_config_value(dagster_type, config_value):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    result = evaluate_config_value(dagster_type, config_value)
    if not result.success:
        raise DagsterEvaluateConfigValueError(
            result.errors[0].stack,
            result.errors[0].message,
        )
    return result.value


def evaluate_config_value(dagster_type, config_value):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    collector = ErrorCollector()
    value = _evaluate_config_value(
        dagster_type,
        config_value,
        EvaluationStack(entries=[]),
        collector,
    )
    if collector.errors:
        return EvaluateValueResult(success=False, value=None, errors=collector.errors)
    else:
        return EvaluateValueResult(success=True, value=value, errors=[])


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


def evaluate_selector_config_value(dagster_type, config_value, collector, stack):
    check.inst_param(dagster_type, 'dagster_type', DagsterSelectorType)
    check.inst_param(collector, 'collector', ErrorCollector)
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value for selector type {type_name} must be a dict got {value}'.format(
                    type_name=dagster_type.name,
                    value=config_value,
                ),
                error_data=RuntimeMismatchErrorData(
                    dagster_type=dagster_type,
                    value_rep=repr(config_value),
                ),
            )
        )
        return None

    if config_value and len(config_value) > 1:
        incoming_fields = sorted(list(config_value.keys()))
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
                error_data=SelectorTypeErrorData(incoming_fields=incoming_fields),
            )
        )
        return None
    elif not config_value:
        defined_fields = sorted(list(dagster_type.field_dict.keys()))
        if len(dagster_type.field_dict) > 1:
            collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                    message=(
                        'Must specify a field if more than one defined. Defined fields: '
                        '{defined_fields}'
                    ).format(defined_fields=defined_fields),
                    error_data=SelectorTypeErrorData(incoming_fields=[]),
                )
            )
            return None

        field_name, field_def = single_item(dagster_type.field_dict)
        incoming_field_value = field_def.default_value if field_def.default_provided else None
    else:
        check.invariant(config_value and len(config_value) == 1)

        field_name, incoming_field_value = single_item(config_value)
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
    field_value = _evaluate_config_value(
        parent_field.dagster_type,
        incoming_field_value,
        stack_with_field(stack, field_name, parent_field),
        collector,
    )

    if collector.errors:
        return None

    return dagster_type.construct_from_config_value({field_name: field_value})


def _evaluate_config_value(dagster_type, config_value, stack, collector):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)
    check.inst_param(stack, 'stack', EvaluationStack)
    check.inst_param(collector, 'collector', ErrorCollector)

    if isinstance(dagster_type, DagsterScalarType):
        if dagster_type.is_python_valid_value(config_value):
            return config_value
        else:
            collector.add_error(
                EvaluationError(
                    stack=stack,
                    reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                    message='Value {value} is not valid for type {type_name}'.format(
                        value=config_value,
                        type_name=dagster_type.name,
                    ),
                    error_data=RuntimeMismatchErrorData(
                        dagster_type=dagster_type,
                        value_rep=repr(config_value),
                    ),
                )
            )
            return None
    elif isinstance(dagster_type, DagsterSelectorType):
        return evaluate_selector_config_value(dagster_type, config_value, collector, stack)
    elif isinstance(dagster_type, DagsterCompositeType):
        return evaluate_composite_config_value(dagster_type, config_value, collector, stack)
    elif isinstance(dagster_type, _DagsterListType):
        return evaluate_list_value(dagster_type, config_value, collector, stack)
    elif isinstance(dagster_type, PythonObjectType):
        check.failed('PythonObjectType should not be used in a config hierarchy')
    elif dagster_type == Any:
        return config_value
    else:
        check.failed('Unknown type {name}'.format(name=dagster_type.name))


def evaluate_list_value(dagster_list_type, config_value, collector, stack):
    check.inst_param(dagster_list_type, 'dagster_list_type', _DagsterListType)
    check.inst_param(collector, 'collector', ErrorCollector)
    check.inst_param(stack, 'stack', EvaluationStack)

    if not config_value:
        return []

    if not isinstance(config_value, list):
        collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value for list type {type_name} must be a list got {value}'.format(
                    type_name=dagster_list_type.name,
                    value=config_value,
                ),
                error_data=RuntimeMismatchErrorData(
                    dagster_type=dagster_list_type,
                    value_rep=repr(config_value),
                ),
            )
        )
        return None

    output_list = []
    for index, item in enumerate(config_value):
        # TODO: how to represent list element in the stack
        # should be pushing something
        # Should consult with mikhail/ben to see about what info is best
        # to expose in dagit. Probably just a list index in the stack
        output_list.append(
            _evaluate_config_value(
                dagster_list_type.inner_type,
                item,
                stack_with_list_index(stack, index),
                collector,
            )
        )

    if collector.errors:
        return None

    return output_list


def evaluate_composite_config_value(dagster_composite_type, config_value, collector, stack):
    check.inst_param(dagster_composite_type, 'dagster_composite_type', DagsterCompositeType)
    check.inst_param(collector, 'collector', ErrorCollector)
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        collector.add_error(
            EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value for composite type {type_name} must be a dict got {value}'.format(
                    type_name=dagster_composite_type.name,
                    value=config_value,
                ),
                error_data=RuntimeMismatchErrorData(
                    dagster_type=dagster_composite_type,
                    value_rep=repr(config_value),
                ),
            )
        )
        return None

    config_value = check.opt_dict_param(config_value, 'incoming_value', key_type=str)

    field_dict = dagster_composite_type.field_dict

    defined_fields = set(field_dict.keys())
    incoming_fields = set(config_value.keys())

    local_errors = []

    for received_field in incoming_fields:
        if received_field not in defined_fields:
            local_errors.append(
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
            local_errors.append(
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
            evaluated_value = _evaluate_config_value(
                field_def.dagster_type,
                config_value[expected_field],
                stack_with_field(stack, expected_field, field_def),
                collector,
            )
            processed_fields[expected_field] = evaluated_value
        elif field_def.default_provided:
            processed_fields[expected_field] = field_def.default_value
        elif not field_def.is_optional:
            check.invariant(
                local_errors,
                'Error should have been added for missing required field',
            )

    if local_errors:
        collector.errors = collector.errors + local_errors
        return None
    else:
        return dagster_composite_type.construct_from_config_value(processed_fields)


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
        error_data=MissingFieldErrorData(
            field_name=expected_field,
            field_def=dagster_type.field_named(expected_field),
        ),
    )
