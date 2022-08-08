from dagster_twilio.version import __version__
from dagster import op


def test_version():
    assert __version__
