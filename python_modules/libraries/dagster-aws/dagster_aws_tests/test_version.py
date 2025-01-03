import os

from dagster_aws.version import __version__


def test_version():
    assert __version__


# Make sure unit tests never connect to real AWS
# https://github.com/getmoto/moto/pull/6807
def test_fake_aws_credentials():
    assert os.environ["AWS_ACCESS_KEY_ID"] == "FOOBARKEY"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "FOOBARSECRET"
