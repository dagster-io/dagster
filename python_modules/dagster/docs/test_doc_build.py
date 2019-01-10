import os
import subprocess

import pytest

from dagster.utils import script_relative_path


BUILT_DOCS_RELATIVE_PATH = '_build/'

def test_build_all_docs(snapshot):
    pwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        subprocess.check_output(['make', 'clean'])
        subprocess.check_output(['make', 'html'])
        os.chdir(script_relative_path(BUILT_DOCS_RELATIVE_PATH))
        snapshot.assert_match(list(os.walk('.')))
    finally:
        os.chdir(pwd)
