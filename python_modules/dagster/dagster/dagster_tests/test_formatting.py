import subprocess
import sys
import os

import pytest

from dagster.utils import script_relative_path


@pytest.mark.skipif(
    sys.version_info < (3, 6),
    reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
    All of the development notebooks currently use the python3 "kernel" so they will
    not be executable in a container that only have python2.7 (e.g. in CircleCI)
    ''',
)
def test_formatting():
    # cwd = os.getcwd()
    # try:
    cmd = 'black {target} --diff --line-length 100 -S --fast'.format(
        target=script_relative_path('..')
    )
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()

    assert p_status == 0
    assert 'reformatted' not in output.decode('utf-8')

    print(output)
    print(p_status)
    #     pass
    # finally:
    #     os.chdir(cwd)
