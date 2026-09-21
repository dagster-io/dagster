import os
import subprocess

from dagster import asset
from dagster._core.test_utils import poll_for_subprocess_output


def test_invoke_cli():
    process = subprocess.Popen(
        ["dagit", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _ = process.communicate()
    assert process.returncode == 0
    assert b"dagster-webserver, version" in stdout


# This makes this module loadable by dagit
@asset
def foo(bar):
    return 1


def test_cli_logs_to_dagit():
    defs_path = os.path.realpath(__file__)
    process = subprocess.Popen(
        ["dagit", "-f", defs_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    marker = b"The `dagit` CLI command is deprecated"
    try:
        stdout, stderr = poll_for_subprocess_output(process, marker, timeout=60)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    captured = stdout.decode("utf-8", errors="replace")
    assert marker.decode() in captured, (
        f"Expected deprecation banner in dagit stdout within 60s. "
        f"stdout={captured!r} "
        f"stderr={stderr.decode('utf-8', errors='replace')!r}"
    )
    assert "- dagit -" in captured
