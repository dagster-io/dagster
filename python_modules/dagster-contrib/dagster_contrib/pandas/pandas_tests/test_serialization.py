from collections import namedtuple
import os
import uuid

import pandas as pd

from dagster_contrib.pandas import DataFrame

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


def test_basic_pandas():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    out_df = roundtrip_typed_value(df, DataFrame)
    assert out_df.equals(df)
