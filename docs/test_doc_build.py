import os
import subprocess
import sys

import pytest

from dagster.utils import file_relative_path


@pytest.mark.docs
@pytest.mark.skipif(sys.version_info < (3, 6), reason="We don't support building docs in python 2")
def test_build_all_docs():
    pwd = os.getcwd()
    try:
        os.chdir(file_relative_path(__file__, '.'))
        subprocess.check_output(['make', 'clean'])
        subprocess.check_output(['make', 'html'])
    finally:
        os.chdir(pwd)
