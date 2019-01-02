import os
import subprocess

from dagster.utils import script_relative_path


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
