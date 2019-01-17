from __future__ import unicode_literals

import subprocess

from dagster.version import __version__


def test_version():
    assert subprocess.check_output(['dagster', '--version']) == bytes(
        ('dagster, version {version}\n'.format(version=__version__)).encode('utf-8')
    )
