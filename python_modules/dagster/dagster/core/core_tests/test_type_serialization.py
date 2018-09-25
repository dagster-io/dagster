import pickle
import os
import uuid
from dagster import types

TempFileStore = types.TempFileStore


def test_basic_serialization():
    base_dir = f'/tmp/dagster/scratch/{str(uuid.uuid4())}'
    os.mkdir(base_dir)
    file_store = TempFileStore(base_dir)
    info = types.Int.serialize_value(file_store, 1)

    with open(info.path) as ff:
        out_value = pickle.load(ff)

        assert out_value == 1
