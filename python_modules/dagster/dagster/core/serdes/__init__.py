'''
Serialization & deserialization for Dagster event objects.

Why have custom serialization?

* Default json serialization doesn't work well on namedtuples, which we use extensively to create
  immutable value types. Namedtuples serialize like tuples as flat lists.
* Explicit whitelisting should help ensure we are only persisting or communicating across a
  serialization boundary the types we expect to.

Why not pickle?

* This isn't meant to replace pickle in the conditions that pickle is reasonable to use
  (in memory, not human readble, etc) just handle the json case effectively.
'''
import json
from enum import Enum

from dagster import check, seven

_WHITELISTED_TUPLE_MAP = {}
_WHITELISTED_ENUM_MAP = {}


def whitelist_for_serdes(klass):
    if issubclass(klass, Enum):
        _WHITELISTED_ENUM_MAP[klass.__name__] = klass
    elif issubclass(klass, tuple):
        _WHITELISTED_TUPLE_MAP[klass.__name__] = klass
    else:
        check.failed('Can not whitelist class {klass} for serdes'.format(klass=klass))
    return klass


def pack_value(val):
    if isinstance(val, list):
        return [pack_value(i) for i in val]
    if isinstance(val, tuple):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in _WHITELISTED_TUPLE_MAP,
            'Can only serialize whitelisted namedtuples, recieved {}'.format(klass_name),
        )
        base_dict = {key: pack_value(value) for key, value in val._asdict().items()}
        base_dict['__class__'] = klass_name
        return base_dict
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in _WHITELISTED_ENUM_MAP,
            'Can only serialize whitelisted Enums, recieved {}'.format(klass_name),
        )
        return {'__enum__': str(val)}
    if isinstance(val, dict):
        return {key: pack_value(value) for key, value in val.items()}

    return val


def serialize_dagster_namedtuple(nt):
    return seven.json.dumps(pack_value(nt))


def unpack_value(val):
    if isinstance(val, list):
        return [unpack_value(i) for i in val]
    if isinstance(val, dict) and val.get('__class__'):
        klass_name = val.pop('__class__')
        klass = _WHITELISTED_TUPLE_MAP[klass_name]
        val = {key: unpack_value(value) for key, value in val.items()}

        return klass(**val)
    if isinstance(val, dict) and val.get('__enum__'):
        name, member = val['__enum__'].split('.')
        return getattr(_WHITELISTED_ENUM_MAP[name], member)
    if isinstance(val, dict):
        return {key: unpack_value(value) for key, value in val.items()}

    return val


def deserialize_json_to_dagster_namedtuple(json_str):
    return unpack_value(json.loads(json_str))
