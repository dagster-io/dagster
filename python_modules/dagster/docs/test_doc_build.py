# py27 compat, see https://stackoverflow.com/a/844443/324449
import io
import os
import re
import subprocess
import sys

import pytest

from dagster.utils import script_relative_path


BUILT_DOCS_RELATIVE_PATH = '_build/'

IGNORE_FILES = [
    '.DS_Store',
    'objects.inv',
    '[A-Z0-9a-z_-]*\\.png',
    '[A-Z0-9a-z_-]*\\.gif',
    '[A-Z0-9a-z_-]*\\.doctree',
    '[A-Z0-9a-z_-]*\\.pickle',
    'searchindex.js',
]


# Right now, these tests fail as soon as a snapshot fails -- and there is no way to see *all* of
# the snapshot failures associated with a diff. We should probably break doc build into a fixture,
# and then figure out a way to either dynamically generate a test case for each snapshot 
# (probably hard since tests are collected before fixtures are executed -- but maybe we can lever
# the checked-in snapshots for this) or collect the test failures and display all of them.
def test_build_all_docs(snapshot):
    pwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        subprocess.check_output(['make', 'clean'])
        subprocess.check_output(['make', 'html'])
        os.chdir(script_relative_path(BUILT_DOCS_RELATIVE_PATH))
        walked = sorted(
            [
                (
                    dirpath,
                    sorted(dirnames),
                    sorted(
                        [
                            filename
                            for filename in filenames
                            if not any((re.match(pattern, filename) for pattern in IGNORE_FILES))
                        ]
                    ),
                )
                for dirpath, dirnames, filenames in os.walk('.')
            ],
            key=lambda x: x[0],
        )
        snapshot.assert_match(walked)
        # The snapshot tests only need to run on py3, because the docs aren't built on py2
        if sys.version_info[0] < 3:
            return

        for dirpath, dirnames, filenames in walked:
            for filename in filenames:
                if any((re.match(pattern, filename) for pattern in IGNORE_FILES)):
                    continue
                # py27 compat
                with io.open(os.path.join(dirpath, filename), mode='r', encoding='utf-8') as fd:
                    try:
                        snapshot.assert_match(fd.read())
                    except UnicodeDecodeError:
                        raise Exception((dirpath, filename))

    finally:
        os.chdir(pwd)
