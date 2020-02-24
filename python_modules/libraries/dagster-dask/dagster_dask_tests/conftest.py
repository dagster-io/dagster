import os

import pytest


@pytest.fixture(scope='session')
def dask_address():
    return os.getenv('DASK_ADDRESS', 'localhost')


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-scratch-80542c2'
