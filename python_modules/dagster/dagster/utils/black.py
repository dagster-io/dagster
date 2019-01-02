import subprocess
import sys

import pytest


def black_test(f):
    return pytest.mark.skipif(
        sys.version_info < (3, 6), reason='Black is 3.6 and above only. Can process all python code'
    )(f)


def perform_black_test(target_dir):
    cmd = 'black {target} --diff --line-length 100 -S --fast'.format(target=target_dir)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, _err) = p.communicate()
    p_status = p.wait()

    assert p_status == 0
    assert 'reformatted' not in output.decode('utf-8')
