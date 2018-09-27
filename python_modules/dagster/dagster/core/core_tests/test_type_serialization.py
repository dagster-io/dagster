from collections import namedtuple
import pickle
import os
import uuid

import pandas as pd

from dagster import types
from dagster.pandas import DataFrame

SomeTuple = namedtuple('SomeTuple', 'foo')


def get_unittest_path():
    base_dir = '/tmp/dagster/scratch/unittests/{uuid}'.format(uuid=str(uuid.uuid4()))
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    return os.path.join(base_dir, 'value.p')


def roundtrip(value):
    full_path = get_unittest_path()

    with open(full_path, 'wb') as wf:
        pickle.dump(value, wf)

    with open(full_path, 'rb') as rf:
        return pickle.load(rf)


def roundtrip_typed_value(value, dagster_type):
    full_path = get_unittest_path()

    with open(full_path, 'wb') as wf:
        dagster_type.serialize_value(wf, value)

    with open(full_path, 'rb') as rf:
        return dagster_type.deserialize_value(rf)


def test_pickle():
    assert roundtrip(1) == 1
    assert roundtrip('foo') == 'foo'


def test_namedtuple_pickle():

    value = SomeTuple(foo='bar')
    assert roundtrip(value) == value


def test_basic_serialization_string():
    assert roundtrip_typed_value('foo', types.String)


def test_basic_serialization():
    assert roundtrip_typed_value(1, types.Int) == 1
    assert roundtrip_typed_value(True, types.Bool) is True
    assert roundtrip_typed_value({'bar': 'foo'}, types.Dict) == {'bar': 'foo'}


def test_pandasmeta_serialization():
    from dagster.pandas import DataFrameMeta

    value = DataFrameMeta(format='csv', path='/tmp/some_path.csv')
    assert roundtrip(value) == value


def test_basic_pandas():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    out_df = roundtrip_typed_value(df, DataFrame)
    assert out_df.equals(df)
