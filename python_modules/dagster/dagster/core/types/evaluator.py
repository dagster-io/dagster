from collections import namedtuple
from enum import Enum

import six

from dagster import check

from dagster.core.errors import DagsterError
from dagster.utils import single_item, make_readonly_value

from .config import ConfigType
from .default_applier import apply_default_values
from .field_utils import check_field_param
from .type_printer import print_config_type_to_string


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class FieldsNotDefinedErrorData(namedtuple('_FieldsNotDefinedErrorData', 'field_names')):
    def __new__(cls, field_names):
        return super(FieldsNotDefinedErrorData, cls).__new__(
            cls, check.list_param(field_names, 'field_names', of_type=str)
        )


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
            check_field_param(field_def, 'field_def'),
        )


class MissingFieldsErrorData(namedtuple('_MissingFieldErrorData', 'field_names field_defs')):
    def __new__(cls, field_names, field_defs):
        return super(MissingFieldsErrorData, cls).__new__(
            cls,
            check.list_param(field_names, 'field_names', of_type=str),
            [check_field_param(field_def, 'field_defs') for field_def in field_defs],
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
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
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
            check_field_param(field_def, 'field_def'),
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

    path_msg, path = _get_friendly_path_info(error.stack)

    type_msg = _get_type_msg(error, type_in_context)

    if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED:
        return 'Undefined field "{field_name}"{type_msg} {path_msg}'.format(
            field_name=error.error_data.field_name, path_msg=path_msg, type_msg=type_msg
        )
    elif error.reason == DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH:
        return 'Type failure at path "{path}"{type_msg}. {message}.'.format(
            path=path, type_msg=type_msg, message=error.message
        )
    elif error.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR:
        return error.message
    else:
        check.failed('{} (friendly message for this type not yet provided)'.format(error.reason))


def _get_type_msg(error, type_in_context):
    if error.stack.type_in_context.is_system_config:
        return ''
    else:
        return ' on type "{type_name}"'.format(type_name=type_in_context.name)


def _get_friendly_path_msg(stack):
    return _get_friendly_path_info(stack)[0]


def _get_friendly_path_info(stack):
    if not stack.entries:
        path = ''
        path_msg = 'at document config root.'
    else:
        comps = ['root']
        for entry in stack.entries:
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

    value = apply_default_values(config_type, config_value)

    return EvaluateValueResult(success=True, value=make_readonly_value(value), errors=[])


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
                message='Value {path_msg} is not valid. Expected "{type_name}"'.format(
                    path_msg=_get_friendly_path_msg(stack), type_name=config_type.name
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
    elif config_type.is_enum:
        errors = validate_enum_value(config_type, config_value, stack)
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))

    for error in errors:
        yield error


def validate_enum_value(enum_type, config_value, stack):
    check.param_invariant(enum_type.is_enum, 'enum_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if not isinstance(config_value, six.string_types):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for enum type {type_name} must be a string'.format(
                type_name=enum_type.name
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=enum_type, value_rep=repr(config_value)
            ),
        )
        return

    if not enum_type.is_valid_config_enum_value(config_value):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value not in enum type {type_name}'.format(type_name=enum_type.name),
            error_data=RuntimeMismatchErrorData(
                config_type=enum_type, value_rep=repr(config_value)
            ),
        )
        return


## Selectors


def validate_selector_config_value(selector_type, config_value, stack):
    check.param_invariant(selector_type.is_selector, 'selector_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for selector type {type_name} must be a dict'.format(
                type_name=selector_type.name
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
                'You can only specify a single field {path_msg}. You specified {incoming_fields}. '
                'The available fields are {defined_fields}'
            ).format(
                incoming_fields=incoming_fields,
                defined_fields=defined_fields,
                path_msg=_get_friendly_path_msg(stack),
            ),
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
                    'Must specify a field {path_msg} if more than one field is defined. '
                    'Defined fields: {defined_fields}'
                ).format(defined_fields=defined_fields, path_msg=_get_friendly_path_msg(stack)),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        field_name, field_def = single_item(selector_type.fields)

        if not field_def.is_optional:
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'Must specify the required field {path_msg}. Defined fields: {defined_fields}'
                ).format(defined_fields=defined_fields, path_msg=_get_friendly_path_msg(stack)),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    else:
        check.invariant(config_value and len(config_value) == 1)

        field_name, incoming_field_value = single_item(config_value)
        if field_name not in selector_type.fields:
            yield create_field_not_defined_error(selector_type, stack, field_name)
            return

    parent_field = selector_type.fields[field_name]
    for error in _validate_config(
        parent_field.config_type,
        incoming_field_value,
        stack_with_field(stack, field_name, parent_field),
    ):
        yield error


## Composites


def validate_composite_config_value(composite_type, config_value, stack):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.is_composite, 'composite_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    path_msg, _path = _get_friendly_path_info(stack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value {path_msg} must be dict. Expected: "{type_name}".'.format(
                path_msg=path_msg,
                type_name=print_config_type_to_string(composite_type, with_lines=False),
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

    # Here, we support permissive composites. In cases where we know the set of permissible keys a
    # priori, we validate against the config. For permissive composites, we give the user an escape
    # hatch where they can specify arbitrary fields...
    if not composite_type.is_permissive_composite:
        undefined_fields = []
        for received_field in incoming_fields:
            if received_field not in defined_fields:
                undefined_fields.append(received_field)

        if undefined_fields:
            if len(undefined_fields) == 1:
                yield create_field_not_defined_error(composite_type, stack, undefined_fields[0])
            else:
                yield create_fields_not_defined_error(composite_type, stack, undefined_fields)

    # ...However, for any fields the user *has* told us about, we validate against their config
    # specifications
    missing_fields = []
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
            missing_fields.append(expected_field)

    if missing_fields:
        if len(missing_fields) == 1:
            yield create_missing_required_field_error(composite_type, stack, missing_fields[0])
        else:
            yield create_missing_required_fields_error(composite_type, stack, missing_fields)


## Lists


def validate_list_value(list_type, config_value, stack):
    check.param_invariant(list_type.is_list, 'list_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if not isinstance(config_value, list):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value {path_msg} must be list. Expected: {type_name}'.format(
                path_msg=_get_friendly_path_msg(stack),
                type_name=print_config_type_to_string(list_type, with_lines=False),
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


def create_fields_not_defined_error(composite_type, stack, undefined_fields):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.has_fields, 'composite_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.list_param(undefined_fields, 'undefined_fields', of_type=str)

    available_fields = sorted(list(composite_type.fields.keys()))
    undefined_fields = sorted(undefined_fields)

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED,
        message=(
            'Fields "{undefined_fields}" are not defined {path_msg} Available '
            'fields: "{available_fields}"'
        ).format(
            undefined_fields=undefined_fields,
            path_msg=_get_friendly_path_msg(stack),
            available_fields=available_fields,
        ),
        error_data=FieldsNotDefinedErrorData(field_names=undefined_fields),
    )


def create_field_not_defined_error(config_type, stack, received_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.str_param(received_field, 'received_field')

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Field "{received}" is not defined {path_msg} Expected: "{type_name}"'.format(
            path_msg=_get_friendly_path_msg(stack),
            type_name=print_config_type_to_string(config_type, with_lines=False),
            received=received_field,
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_missing_required_field_error(config_type, stack, expected_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.str_param(expected_field, 'expected_field')

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required field "{expected}" {path_msg} Available Fields: '
            '"{available_fields}".'
        ).format(
            expected=expected_field,
            path_msg=_get_friendly_path_msg(stack),
            available_fields=sorted(list(config_type.fields.keys())),
        ),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_def=config_type.fields[expected_field]
        ),
    )


def create_missing_required_fields_error(composite_type, stack, missing_fields):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.has_fields, 'compositve_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.list_param(missing_fields, 'missing_fields', of_type=str)

    missing_fields = sorted(missing_fields)
    missing_field_defs = list(map(lambda mf: composite_type.fields[mf], missing_fields))

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS,
        message='Missing required fields "{missing_fields}" {path_msg}".'.format(
            missing_fields=missing_fields, path_msg=_get_friendly_path_msg(stack)
        ),
        error_data=MissingFieldsErrorData(
            field_names=missing_fields, field_defs=missing_field_defs
        ),
    )
