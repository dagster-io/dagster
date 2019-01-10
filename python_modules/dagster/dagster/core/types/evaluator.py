from collections import namedtuple
from enum import Enum

from dagster import check

from dagster.core.errors import DagsterError

from .config import ConfigType
from .field import Field


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class FieldNotDefinedErrorData(namedtuple('_FieldNotDefinedErrorData', 'field_name')):
    def __new__(cls, field_name):
        return super(FieldNotDefinedErrorData, cls).__new__(
            cls, check.str_param(field_name, 'field_name')
        )


class MissingFieldErrorData(namedtuple('_MissingFieldErrorData', 'field_name field_def')):
    def __new__(cls, field_name, field_def):
        return super(MissingFieldErrorData, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check.inst_param(field_def, 'field_def', Field),
        )


class RuntimeMismatchErrorData(namedtuple('_RuntimeMismatchErrorData', 'config_type value_rep')):
    def __new__(cls, config_type, value_rep):
        return super(RuntimeMismatchErrorData, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.str_param(value_rep, 'value_rep'),
        )


class SelectorTypeErrorData(namedtuple('_SelectorTypeErrorData', 'dagster_type incoming_fields')):
    def __new__(cls, dagster_type, incoming_fields):
        check.param_invariant(dagster_type.is_selector, 'dagster_type')
        return super(SelectorTypeErrorData, cls).__new__(
            cls, dagster_type, check.list_param(incoming_fields, 'incoming_fields', of_type=str)
        )


ERROR_DATA_TYPES = (
    FieldNotDefinedErrorData,
    MissingFieldErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)


class EvaluationStack(namedtuple('_EvaluationStack', 'config_type entries')):
    def __new__(cls, config_type, entries):
        return super(EvaluationStack, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.list_param(entries, 'entries', of_type=EvaluationStackEntry),
        )

    @property
    def levels(self):
        return [
            entry.field_name
            for entry in self.entries
            if isinstance(entry, EvaluationStackPathEntry)
        ]

    @property
    def type_in_context(self):
        ttype = self.entries[-1].config_type if self.entries else self.config_type
        # TODO: This is the wrong place for this
        # Should have general facility for unwrapping named types
        if ttype.is_nullable:
            return ttype.inner_type
        else:
            return ttype


class EvaluationStackEntry:  # marker interface
    pass


class EvaluationStackPathEntry(
    namedtuple('_EvaluationStackEntry', 'field_name field_def'), EvaluationStackEntry
):
    def __new__(cls, field_name, field_def):
        return super(EvaluationStackPathEntry, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check.inst_param(field_def, 'field_def', Field),
        )

    @property
    def config_type(self):
        return self.field_def.config_type


class EvaluationStackListItemEntry(
    namedtuple('_EvaluationStackListItemEntry', 'config_type list_index'), EvaluationStackEntry
):
    def __new__(cls, config_type, list_index):
        check.int_param(list_index, 'list_index')
        check.param_invariant(list_index >= 0, 'list_index')
        return super(EvaluationStackListItemEntry, cls).__new__(
            cls, check.inst_param(config_type, 'config_type', ConfigType), list_index
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


def friendly_string_for_error(error):
    type_in_context = error.stack.type_in_context

    path_msg, path = _get_friendly_path_info(error)

    type_msg = _get_type_msg(error, type_in_context)

    if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD:
        return 'Missing required field "{field_name}"{type_msg} {path_msg}'.format(
            field_name=error.error_data.field_name, path_msg=path_msg, type_msg=type_msg
        )
    elif error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED:
        return 'Undefined field "{field_name}"{type_msg} {path_msg}'.format(
            field_name=error.error_data.field_name, path_msg=path_msg, type_msg=type_msg
        )
    elif error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH:
        return 'Type failure at path "{path}"{type_msg}. Got "{value_rep}".'.format(
            path=path, type_msg=type_msg, value_rep=error.error_data.value_rep
        )
    elif error.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR:
        if error.error_data.incoming_fields:
            return (
                'Specified more than one field at path "{path}". '
                'You can only specify one field at this level.'
            ).format(path=path)
        else:
            return (
                'You specified no fields at path "{path}". '
                'You must specify one and only one field at this level.'
            ).format(path=path)
    else:
        check.failed('not supported')


def _get_type_msg(error, type_in_context):
    if error.stack.type_in_context.is_system_config:
        return ''
    else:
        return ' on type "{type_name}"'.format(type_name=type_in_context.name)


def _get_friendly_path_info(error):
    if not error.stack.entries:
        path = ''
        path_msg = 'at document config root.'
    else:
        comps = ['root']
        for entry in error.stack.entries:
            if isinstance(entry, EvaluationStackPathEntry):
                comp = ':' + entry.field_name
                comps.append(comp)
            elif isinstance(entry, EvaluationStackListItemEntry):
                comps.append('[{i}]'.format(i=entry.list_index))
            else:
                check.failed('unsupported')

        path = ''.join(comps)
        path_msg = 'at path ' + path
    return path_msg, path


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


def stack_with_field(stack, field_name, field_def):
    return EvaluationStack(
        config_type=stack.config_type,
        entries=stack.entries + [EvaluationStackPathEntry(field_name, field_def)],
    )


def stack_with_list_index(stack, list_index):
    list_type = stack.type_in_context
    check.invariant(list_type.is_list)
    return EvaluationStack(
        config_type=stack.config_type,
        entries=stack.entries + [EvaluationStackListItemEntry(list_type.inner_type, list_index)],
    )


def hard_create_config_value(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)
    result = evaluate_config_value(config_type, config_value)
    check.invariant(result.success)
    return result.value


def evaluate_config_value(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)
    errors = validate_config(config_type, config_value)
    if errors:
        return EvaluateValueResult(success=False, value=None, errors=errors)

    value = deserialize_config(config_type, config_value)

    return EvaluateValueResult(success=True, value=value, errors=[])


def validate_config(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)

    return list(
        _validate_config(
            config_type, config_value, EvaluationStack(config_type=config_type, entries=[])
        )
    )


def _validate_config(config_type, config_value, stack):
    check.inst_param(config_type, 'config_type', ConfigType)
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_type.is_scalar:
        if not config_type.is_config_scalar_valid(config_value):
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value {value} is not valid for type {type_name}'.format(
                    value=config_value, type_name=config_type.name
                ),
                error_data=RuntimeMismatchErrorData(
                    config_type=config_type, value_rep=repr(config_value)
                ),
            )
        return

    errors = []

    if config_type.is_any:
        # no-op: we're safe
        return
    elif config_type.is_selector:
        errors = validate_selector_config_value(config_type, config_value, stack)
    elif config_type.is_composite:
        errors = validate_composite_config_value(config_type, config_value, stack)
    elif config_type.is_list:
        errors = validate_list_value(config_type, config_value, stack)
    elif config_type.is_nullable:
        errors = (
            []
            if config_value is None
            else _validate_config(config_type.inner_type, config_value, stack)
        )
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))

    for error in errors:
        yield error


def deserialize_config(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)
    return _deserialize_config(config_type, config_value)


def _deserialize_config(config_type, config_value):
    if config_type.is_scalar:
        return config_value
    elif config_type.is_selector:
        return deserialize_selector_config(config_type, config_value)
    elif config_type.is_composite:
        return deserialize_composite_config_value(config_type, config_value)
    elif config_type.is_list:
        return deserialize_list_value(config_type, config_value)
    elif config_type.is_nullable:
        if config_value is None:
            return None
        return _deserialize_config(config_type.inner_type, config_value)
    elif config_type.is_any:
        return config_value
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))


## Selectors


def single_item(ddict):
    check.dict_param(ddict, 'ddict')
    check.param_invariant(len(ddict) == 1, 'ddict')
    return list(ddict.items())[0]


def validate_selector_config_value(selector_type, config_value, stack):
    check.param_invariant(selector_type.is_selector, 'selector_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for selector type {type_name} must be a dict got {value}'.format(
                type_name=selector_type.name, value=config_value
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=selector_type, value_rep=repr(config_value)
            ),
        )
        return

    if config_value and len(config_value) > 1:
        incoming_fields = sorted(list(config_value.keys()))
        defined_fields = sorted(list(selector_type.fields.keys()))
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
            message=(
                'You can only specify a single field. You specified {incoming_fields}. '
                'The available fields are {defined_fields}'
            ).format(incoming_fields=incoming_fields, defined_fields=defined_fields),
            error_data=SelectorTypeErrorData(
                dagster_type=selector_type, incoming_fields=incoming_fields
            ),
        )
        return

    elif not config_value:
        defined_fields = sorted(list(selector_type.fields.keys()))
        if len(selector_type.fields) > 1:
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'Must specify a field if more one defined. Defined fields: ' '{defined_fields}'
                ).format(defined_fields=defined_fields),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        field_name, field_def = single_item(selector_type.fields)

        if not field_def.is_optional:
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'Must specify the required field. Defined fields: ' '{defined_fields}'
                ).format(defined_fields=defined_fields),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    else:
        check.invariant(config_value and len(config_value) == 1)

        field_name, incoming_field_value = single_item(config_value)
        if field_name not in selector_type.fields:
            yield create_field_not_defined_error(
                selector_type, stack, set(selector_type.fields.keys()), field_name
            )
            return

    parent_field = selector_type.fields[field_name]
    for error in _validate_config(
        parent_field.config_type,
        incoming_field_value,
        stack_with_field(stack, field_name, parent_field),
    ):
        yield error


def deserialize_selector_config(selector_type, config_value):
    check.param_invariant(selector_type.is_selector, 'selector_type')

    if config_value:
        check.invariant(config_value and len(config_value) == 1)
        field_name, incoming_field_value = single_item(config_value)

    else:
        field_name, field_def = single_item(selector_type.fields)
        incoming_field_value = field_def.default_value if field_def.default_provided else None

    parent_field = selector_type.fields[field_name]
    field_value = _deserialize_config(parent_field.config_type, incoming_field_value)
    return {field_name: field_value}


## Composites


def validate_composite_config_value(composite_type, config_value, stack):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.is_composite, 'composite_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for composite type {type_name} must be a dict got {value}'.format(
                type_name=composite_type.name, value=config_value
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=composite_type, value_rep=repr(config_value)
            ),
        )
        return

    # ASK: this can crash on user error
    config_value = check.opt_dict_param(config_value, 'incoming_value', key_type=str)

    fields = composite_type.fields

    defined_fields = set(fields.keys())
    incoming_fields = set(config_value.keys())

    for received_field in incoming_fields:
        if received_field not in defined_fields:
            yield create_field_not_defined_error(
                composite_type, stack, defined_fields, received_field
            )

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            for error in _validate_config(
                field_def.config_type,
                config_value[expected_field],
                stack_with_field(stack, expected_field, field_def),
            ):
                yield error

        elif field_def.is_optional:
            pass

        else:
            check.invariant(not field_def.default_provided)
            yield create_missing_required_field_error(
                composite_type, stack, defined_fields, expected_field
            )


def deserialize_composite_config_value(composite_type, config_value):
    check.param_invariant(composite_type.is_composite, 'composite_type')

    # ASK: this can crash on user error
    config_value = check.opt_dict_param(config_value, 'config_value', key_type=str)

    fields = composite_type.fields
    incoming_fields = set(config_value.keys())

    processed_fields = {}

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            processed_fields[expected_field] = _deserialize_config(
                field_def.config_type, config_value[expected_field]
            )

        elif field_def.default_provided:
            processed_fields[expected_field] = field_def.default_value

        elif not field_def.is_optional:
            check.failed('Missing non-optional composite member not caught in validation')

    return processed_fields


## Lists


def validate_list_value(list_type, config_value, stack):
    check.param_invariant(list_type.is_list, 'list_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if not isinstance(config_value, list):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for list type {type_name} must be a list got {value}'.format(
                type_name=list_type.name, value=config_value
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=list_type, value_rep=repr(config_value)
            ),
        )
        return

    for index, item in enumerate(config_value):
        for error in _validate_config(
            list_type.inner_type, item, stack_with_list_index(stack, index)
        ):
            yield error


def deserialize_list_value(list_type, config_value):
    check.param_invariant(list_type.is_list, 'list_type')

    if not config_value:
        return []

    return [_deserialize_config(list_type.inner_type, item) for item in config_value]


##


def create_field_not_defined_error(config_type, stack, defined_fields, received_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Field "{received}" is not defined on "{type_name}" Defined {defined}'.format(
            type_name=config_type.name, defined=repr(defined_fields), received=received_field
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_missing_required_field_error(config_type, stack, defined_fields, expected_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required field "{expected}" on "{type_name}". ' 'Defined fields: {defined}'
        ).format(expected=expected_field, type_name=config_type.name, defined=repr(defined_fields)),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_def=config_type.fields[expected_field]
        ),
    )
