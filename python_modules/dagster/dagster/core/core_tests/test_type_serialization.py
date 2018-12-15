from collections import namedtuple
import pickle
import os
import uuid

from dagster import types

SomeTuple = namedtuple('SomeTuple', 'foo')


def get_unittest_path():
    base_dir = '/tmp/dagster/scratch/unittests/{uuid}'.format(uuid=str(uuid.uuid4()))
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    return base_dir


def roundtrip_typed_value(value, dagster_type):
    full_path = get_unittest_path()

    dagster_type.serialize_value(full_path, value)
    return dagster_type.deserialize_value(full_path)


def test_basic_serialization_string():
    assert roundtrip_typed_value('foo', types.String)


def test_basic_serialization():
    assert roundtrip_typed_value(1, types.Int) == 1
    assert roundtrip_typed_value(True, types.Bool) is True
    assert roundtrip_typed_value({'bar': 'foo'}, types.PythonDict) == {'bar': 'foo'}
