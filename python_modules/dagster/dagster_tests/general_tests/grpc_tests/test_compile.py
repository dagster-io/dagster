import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 6), reason="black is not available for python < 3.6")
def test_compiled_protobuf():
    expected_status = subprocess.check_output(["git", "status", "--porcelain"])
    subprocess.check_output([sys.executable, "-m", "dagster.grpc.compile"])
    assert expected_status == subprocess.check_output(["git", "status", "--porcelain"])
