# encoding: utf-8
import hashlib
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, Optional, Sequence, Type

import dagster._check as check
from dagster._annotations import public
from dagster._config.field import normalize_field
from dagster._core.errors import DagsterInvalidConfigDefinitionError

if TYPE_CHECKING:
    from dagster._config.config_type import ConfigType

COMPOSITE_TYPE_MEMOIZATION_CACHE: Dict[str, ConfigType] = {}


def memoize_composite_type(passed_cls: Type[ConfigType], defined_cls: Type[ConfigType], fields: Mapping[str, object], description: Optional[str] = None, field_aliases: Optional[Mapping[str, str]] = None):
    cache_key = _get_cache_key_for_composite_type(defined_cls, fields, description, field_aliases)
    if cache_key in COMPOSITE_TYPE_MEMOIZATION_CACHE:
        return COMPOSITE_TYPE_MEMOIZATION_CACHE[cache_key]

    defined_cls_inst = super(defined_cls, passed_cls).__new__(defined_cls)
    defined_cls_inst._initialized = False  # pylint: disable=protected-access
    COMPOSITE_TYPE_MEMOIZATION_CACHE[cache_key] = defined_cls_inst
    return defined_cls_inst

def _get_cache_key_for_composite_type(cls: Type[Any], fields: Optional[Mapping[str, object]] = None, description: Optional[str] = None, field_aliases: Optional[Mapping[str, str]] = None) -> str:
    return (
        ".".join([cls.__name__, _compute_fields_hash(fields, description, field_aliases)])
        if fields is not None
        else cls.__name__
    )


def _compute_fields_hash(fields: Mapping[str, object], description: Optional[str] = None, field_aliases: Optional[Mapping[str, str]] = None) -> str:

    _fields = { key: normalize_field(value) for key, value in fields.items() }

    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    if description:
        _add_hash(m, f":description: {description}")

    for field_name in sorted(list(_fields.keys())):
        field = _fields[field_name]
        _add_hash(m, f":fieldname: {field_name}")
        if field.default_provided:
            _add_hash(m, f":default_value: {field.default_value_as_json_str}")
        _add_hash(m, f":is_required: {field.is_required}")
        _add_hash(m, f":type_key: {field.config_type.key}")
        if field.description:
            _add_hash(m, f":description: {field.description}")

    field_aliases = check.opt_dict_param(
        field_aliases, "field_aliases", key_type=str, value_type=str
    )
    for field_name in sorted(list(field_aliases.keys())):
        field_alias = field_aliases[field_name]
        _add_hash(m, f":fieldname: {field_name}")
        _add_hash(m, f":fieldalias: {field_alias}")

    return m.hexdigest()

def _add_hash(m, string):
    m.update(string.encode("utf-8"))
