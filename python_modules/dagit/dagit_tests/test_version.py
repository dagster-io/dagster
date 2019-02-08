from __future__ import unicode_literals

import subprocess

from dagit.version import __version__


def test_version():
    assert subprocess.check_output(['dagit', '--version']).decode('utf-8').strip('\n').strip(
        '\r'
    ) == 'dagit, version {version}'.format(version=__version__)
