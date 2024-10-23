import shutil
from os.path import dirname, join, realpath

import pytest


@pytest.fixture
def src_dir():
    return join(dirname(realpath(__file__)), "datasets")


@pytest.fixture
def expected_dir():
    return join(dirname(realpath(__file__)), "expected")


@pytest.fixture(scope="session")
def output_dir():
    out_dir = realpath(join(dirname(realpath(__file__)), "..", "output"))
    shutil.rmtree(out_dir, ignore_errors=True)
    return out_dir
