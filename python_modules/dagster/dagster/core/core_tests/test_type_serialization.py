import pickle
import os
import uuid
from dagster import types

TempFileStore = types.TempFileStore


def roundtrip(value):
    base_dir = f'/tmp/dagster/scratch/unittests/{str(uuid.uuid4())}'
    os.mkdir(base_dir)
    full_path = os.path.join(base_dir, 'value.p')

    with open(full_path, 'wb') as wf:
        pickle.dump(value, wf)

    with open(full_path, 'rb') as rf:
        return pickle.load(rf)


def roundtrip_typed_value(value, dagster_type):
    base_dir = f'/tmp/dagster/scratch/unittests/{str(uuid.uuid4())}'
    os.mkdir(base_dir)
    full_path = os.path.join(base_dir, 'value.p')

    with open(full_path, 'wb') as wf:
        dagster_type.serialize_value(wf, value)

    with open(full_path, 'rb') as rf:
        return dagster_type.deserialize_value(rf)


def test_pickle():
    assert roundtrip(1) == 1
    assert roundtrip('foo') == 'foo'


def test_basic_serialization_string():
    assert roundtrip_typed_value('foo', types.String)


def test_basic_serialization():
    assert roundtrip_typed_value(1, types.Int)
    assert roundtrip_typed_value(True, types.Bool)
    assert roundtrip_typed_value({'bar': 'foo'}, types.Dict)
