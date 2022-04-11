import subprocess
import sys


def test_compiled_protobuf(tmp_path):
    # Will error if exit code is non-zero
    subprocess.check_output([sys.executable, "-m", "dagster.grpc.compile", tmp_path])
