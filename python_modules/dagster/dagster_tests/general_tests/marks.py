import os

import pytest


def aws_credentials_present():
    return os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")


aws = pytest.mark.skipif(not aws_credentials_present(), reason="Couldn't find AWS credentials")

nettest = pytest.mark.nettest
