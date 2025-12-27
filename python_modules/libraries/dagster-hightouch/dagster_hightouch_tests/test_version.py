from importlib.metadata import version

import dagster_hightouch


def test_version():
    assert version("dagster-hightouch") == dagster_hightouch.__version__
