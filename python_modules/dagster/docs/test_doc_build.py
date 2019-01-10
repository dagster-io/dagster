import os
import re
import subprocess

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
]


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
            key=lambda x: x[0]
        )
        snapshot.assert_match(walked)
        for dirpath, dirnames, filenames in walked:
            for filename in filenames:
                if any((re.match(pattern, filename) for pattern in IGNORE_FILES)):
                    continue
                with open(os.path.join(dirpath, filename), 'r') as fd:
                    try:
                        snapshot.assert_match(fd.read())
                    except UnicodeDecodeError:
                        raise Exception((dirpath, filename))

    finally:
        os.chdir(pwd)
