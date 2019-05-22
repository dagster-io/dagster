import sys

import pytest


notebook_test = pytest.mark.skipif(
    sys.version_info < (3, 5),
    reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
)
