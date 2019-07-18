import pytest

import os


@pytest.fixture(scope='session')
def dask_address():
    return os.getenv('DASK_ADDRESS', 'localhost')
