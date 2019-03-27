import re
import subprocess

import pytest


# Dagstermill tests invoke notebooks that look for an ipython kernel called dagster -- if this is
# not already present, then the tests fail. This fixture creates the kernel if it is not already
# present before tests run.
@pytest.fixture(scope='session', autouse=True)
def kernel():
    installed_kernels = [
        x.split(' ')[0]
        for x in [
            re.sub('  +', ' ', x.strip(' '))
            for x in filter(
                lambda x: x.startswith('  '),
                subprocess.check_output(['ipython', 'kernelspec', 'list'])
                .decode('utf-8')
                .split('\n'),
            )
        ]
    ]
    if 'dagster' not in installed_kernels:
        subprocess.check_output(['ipython', 'kernel', 'install', '--name', 'dagster', '--user'])
