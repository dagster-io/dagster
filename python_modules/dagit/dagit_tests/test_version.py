from __future__ import unicode_literals

import subprocess

from dagit.version import __version__


def test_version():
    assert subprocess.check_output(['dagit', '--version']) == bytes(
        ('dagit, version {version}\n'.format(version=__version__)).encode('utf-8')
    )
