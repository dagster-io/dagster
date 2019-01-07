import os
import subprocess
from dagster.utils import script_relative_path


def test_build_all_docs():
    pwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        subprocess.check_output(['make', 'clean'])
        subprocess.check_output(['make', 'html'])
    finally:
        os.chdir(pwd)
