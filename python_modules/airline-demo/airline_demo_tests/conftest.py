import os
import subprocess
import sys

import pytest

from dagster.utils import pushd, script_relative_path


CIRCLECI = os.getenv('CIRCLECI')


@pytest.fixture(scope='session')
def docker_compose_db():
    if sys.version_info.major == 3 and sys.version_info.minor == 7 and CIRCLECI:
        return

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'up', '-d', 'db'])

    yield

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'stop', 'db'])


subprocess.check_output(['docker-compose', 'rm', '-f', 'db'])
