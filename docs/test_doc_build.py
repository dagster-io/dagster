import os
import subprocess
import sys

import pytest

from dagster.utils import script_relative_path


@pytest.mark.docs
@pytest.mark.skipif(sys.version_info < (3, 6), reason="We don't support building docs in python 2")
def test_build_all_docs():
    pwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        subprocess.check_output(['make', 'clean'])
        subprocess.check_output(['make', 'html'])
    finally:
        os.chdir(pwd)
