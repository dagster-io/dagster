from __future__ import unicode_literals

import subprocess

from dagster.version import __version__


def test_version():
    assert subprocess.check_output(['dagster', '--version']).strip('\n').strip('\r') == bytes(
        ('dagster, version {version}'.format(version=__version__)).encode('utf-8')
    )
