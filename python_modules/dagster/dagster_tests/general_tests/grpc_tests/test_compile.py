import subprocess
import sys

import pytest


def test_compiled_protobuf():
    expected_status = subprocess.check_output(["git", "status", "--porcelain"])
    subprocess.check_output([sys.executable, "-m", "dagster.grpc.compile"])
    assert expected_status == subprocess.check_output(["git", "status", "--porcelain"])
