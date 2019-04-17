from __future__ import unicode_literals

import subprocess

from dagit.version import __version__


def test_version():
    assert __version__
