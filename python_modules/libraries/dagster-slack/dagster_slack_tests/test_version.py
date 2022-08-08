from dagster_slack.version import __version__
from dagster import op


def test_version():
    assert __version__
