# encoding: utf-8
import hashlib
from typing import Any, Dict

from dagster import check
from dagster.core.errors import DagsterInvalidConfigDefinitionError

from .config_type import ConfigType, ConfigTypeKind


def all_optional_type(config_type):
    check.inst_param(config_type, "config_type", ConfigType)

    if ConfigTypeKind.is_shape(config_type.kind):
        for field in config_type.fields.values():
            if field.is_required:
                return False
        return True

    if ConfigTypeKind.is_selector(config_type.kind):
        if len(config_type.fields) == 1:
            for field in config_type.fields.values():
                if field.is_required:
                    return False
            return True

    return False


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, **kwargs):
        self.fields = expand_fields_dict(fields)
        super(_ConfigHasFields, self).__init__(**kwargs)


FIELD_HASH_CACHE: Dict[str, Any] = {}


def _memoize_inst_in_field_cache(passed_cls, defined_cls, key):
    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    defined_cls_inst = super(defined_cls, passed_cls).__new__(defined_cls)

    FIELD_HASH_CACHE[key] = defined_cls_inst
    return defined_cls_inst


def _add_hash(m, string):
    m.update(string.encode("utf-8"))


def _compute_fields_hash(fields, description):

    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    if description:
        _add_hash(m, ":description: " + description)

    for field_name in sorted(list(fields.keys())):
        field = fields[field_name]
        _add_hash(m, ":fieldname:" + field_name)
        if field.default_provided:
            _add_hash(m, ":default_value: " + field.default_value_as_json_str)
        _add_hash(m, ":is_required: " + str(field.is_required))
        _add_hash(m, ":type_key: " + field.config_type.key)
        if field.description:
            _add_hash(m, ":description: " + field.description)

    return m.hexdigest()


def _define_shape_key_hash(fields, description):
    return "Shape." + _compute_fields_hash(fields, description)


class Shape(_ConfigHasFields):
    """Schema for configuration data with string keys and typed values via :py:class:`Field`.

    Unlike :py:class:`Permissive`, unspecified fields are not allowed and will throw a
    :py:class:`~dagster.DagsterInvalidConfigError`.

    Args:
        fields (Dict[str, Field]):
            The specification of the config dict.
    """

    def __new__(
        cls,
        fields,
        description=None,
    ):
        return _memoize_inst_in_field_cache(
            cls,
            Shape,
            _define_shape_key_hash(expand_fields_dict(fields), description),
        )

    def __init__(self, fields, description=None):
        fields = expand_fields_dict(fields)
        super(Shape, self).__init__(
            kind=ConfigTypeKind.STRICT_SHAPE,
            key=_define_shape_key_hash(fields, description),
            description=description,
            fields=fields,
        )


def _define_permissive_dict_key(fields, description):
    return (
        "Permissive." + _compute_fields_hash(fields, description=description)
        if fields
        else "Permissive"
    )


class Permissive(_ConfigHasFields):
    """Defines a config dict with a partially specified schema.

    A permissive dict allows partial specification of the config schema. Any fields with a
    specified schema will be type checked. Other fields will be allowed, but will be ignored by
    the type checker.

    Args:
        fields (Dict[str, Field]): The partial specification of the config dict.

    **Examples:**

    .. code-block:: python

        @solid(config_schema=Field(Permissive({'required': Field(String)})))
        def partially_specified_config(context) -> List:
            return sorted(list(context.solid_config.items()))
    """

    def __new__(cls, fields=None, description=None):
        return _memoize_inst_in_field_cache(
            cls,
            Permissive,
            _define_permissive_dict_key(
                expand_fields_dict(fields) if fields else None, description
            ),
        )

    def __init__(self, fields=None, description=None):
        fields = expand_fields_dict(fields) if fields else None
        super(Permissive, self).__init__(
            key=_define_permissive_dict_key(fields, description),
            kind=ConfigTypeKind.PERMISSIVE_SHAPE,
            fields=fields or dict(),
            description=description,
        )


def _define_selector_key(fields, description):
    return "Selector." + _compute_fields_hash(fields, description=description)


class Selector(_ConfigHasFields):
    """Define a config field requiring the user to select one option.

    Selectors are used when you want to be able to present several different options in config but
    allow only one to be selected. For example, a single input might be read in from either a csv
    file or a parquet file, but not both at once.

    Note that in some other type systems this might be called an 'input union'.

    Functionally, a selector is like a :py:class:`Dict`, except that only one key from the dict can
    be specified in valid config.

    Args:
        fields (Dict[str, Field]): The fields from which the user must select.

    **Examples:**

    .. code-block:: python

        @solid(
            config_schema=Field(
                Selector(
                    {
                        'haw': {'whom': Field(String, default_value='honua', is_required=False)},
                        'cn': {'whom': Field(String, default_value='世界', is_required=False)},
                        'en': {'whom': Field(String, default_value='world', is_required=False)},
                    }
                ),
                is_required=False,
                default_value={'en': {'whom': 'world'}},
            )
        )
        def hello_world_with_default(context):
            if 'haw' in context.solid_config:
                return 'Aloha {whom}!'.format(whom=context.solid_config['haw']['whom'])
            if 'cn' in context.solid_config:
                return '你好，{whom}!'.format(whom=context.solid_config['cn']['whom'])
            if 'en' in context.solid_config:
                return 'Hello, {whom}!'.format(whom=context.solid_config['en']['whom'])
    """

    def __new__(cls, fields, description=None):
        return _memoize_inst_in_field_cache(
            cls,
            Selector,
            _define_selector_key(expand_fields_dict(fields), description),
        )

    def __init__(self, fields, description=None):
        fields = expand_fields_dict(fields)
        super(Selector, self).__init__(
            key=_define_selector_key(fields, description),
            kind=ConfigTypeKind.SELECTOR,
            fields=fields,
            description=description,
        )


# Config syntax expansion code below


def is_potential_field(potential_field):
    from .field import Field, resolve_to_config_type

    return isinstance(potential_field, (Field, dict, list)) or resolve_to_config_type(
        potential_field
    )


def convert_fields_to_dict_type(fields):
    return _convert_fields_to_dict_type(fields, fields, [])


def _convert_fields_to_dict_type(original_root, fields, stack):
    return Shape(_expand_fields_dict(original_root, fields, stack))


def expand_fields_dict(fields):
    return _expand_fields_dict(fields, fields, [])


def _expand_fields_dict(original_root, fields, stack):
    check.dict_param(fields, "fields")
    return {
        name: _convert_potential_field(original_root, value, stack + [name])
        for name, value in fields.items()
    }


def expand_list(original_root, the_list, stack):
    from .config_type import Array

    if len(the_list) != 1:
        raise DagsterInvalidConfigDefinitionError(
            original_root, the_list, stack, "List must be of length 1"
        )

    inner_type = _convert_potential_type(original_root, the_list[0], stack)
    if not inner_type:
        raise DagsterInvalidConfigDefinitionError(
            original_root,
            the_list,
            stack,
            "List have a single item and contain a valid type i.e. [int]. Got item {}".format(
                repr(the_list[0])
            ),
        )

    return Array(inner_type)


def convert_potential_field(potential_field):
    return _convert_potential_field(potential_field, potential_field, [])


def _convert_potential_type(original_root, potential_type, stack):
    from .field import resolve_to_config_type

    if isinstance(potential_type, dict):
        return Shape(_expand_fields_dict(original_root, potential_type, stack))

    if isinstance(potential_type, list):
        return expand_list(original_root, potential_type, stack)

    return resolve_to_config_type(potential_type)


def _convert_potential_field(original_root, potential_field, stack):
    from .field import Field

    if potential_field is None:
        raise DagsterInvalidConfigDefinitionError(
            original_root, potential_field, stack, reason="Fields cannot be None"
        )

    if not is_potential_field(potential_field):
        raise DagsterInvalidConfigDefinitionError(original_root, potential_field, stack)

    if isinstance(potential_field, Field):
        return potential_field

    return Field(_convert_potential_type(original_root, potential_field, stack))
