import subprocess

import pytest


@pytest.fixture(scope='session', autouse=True)
def kernel():
    subprocess.check_output(['ipython', 'kernel', 'install', '--name', 'dagster', '--user'])
